from __future__ import absolute_import
import argparse
import sys
import os
import json
import imp
import traceback
import tempfile
import six
from collections import OrderedDict
from itertools import chain
from ..ast import source_parser
from ..utils import is_upload, expand_iterable
from .base import BaseParser, parse_args_monkeypatch, ClintoArgumentParserException, update_dict_copy


# input attributes we try to set:
# checked, name, type, value
# extra information we want to append:
# help,
# required,
# param (for executing the script and knowing if we need - or --),
# upload (boolean providing info on whether it's a file are we uploading or saving)
# choices (for selections)
# choice_limit (for multi selection)

CHOICE_LIMIT_MAP = {'?': '1', '+': '>=1', '*': '>=0'}

# We want to map to model fields as well as html input types we encounter in argparse
# keys are known variable types, as defined in __builtins__
# the model is a Django based model, which can be fitted in the future for other frameworks.
# The type is the HTML input type
# nullcheck is a function to determine if the default value should be checked  (for cases like default='' for strings)
# the attr_kwargs is a mapping of the action attributes to its related html input type. It is a dict
# of the form: {'name_for_html_input': {
# and either one or both of:
#  'action_name': 'attribute_name_on_action', 'callback': 'function_to_evaluate_action_and_return_value'} }

GLOBAL_ATTRS = ['model', 'type']

def get_parameter_action(action):
    """
    To foster a general schema that can accomodate multiple parsers, the general behavior here is described
    rather than the specific language of a given parser. For instance, the 'append' action of an argument
    is collapsing each argument given to a single argument. It also returns a set of actions as well, since
    presumably some actions can impact multiple parameter options
    """
    actions = set()
    if isinstance(action, argparse._AppendAction):
        actions.add('collapse_arguments')
    return actions

GLOBAL_ATTR_KWARGS = {
    'name': {'action_name': 'dest'},
    'value': {'action_name': 'default'},
    'required': {'action_name': 'required'},
    'help': {'action_name': 'help'},
    'param': {'callback': lambda x: x.option_strings[0] if x.option_strings else ''},
    'param_action': {'callback': lambda x: get_parameter_action(x)},
    'choices': {'callback': lambda x: expand_iterable(x.choices)},
    'choice_limit': {'callback': lambda x: CHOICE_LIMIT_MAP.get(x.nargs, x.nargs)}
    }

TYPE_FIELDS = {
    # Python Builtins
    bool: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
    float: {'model': 'FloatField', 'type': 'text', 'html5-type': 'number', 'nullcheck': lambda x: x.default is None,
            'attr_kwargs': GLOBAL_ATTR_KWARGS},
    int: {'model': 'IntegerField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    None: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    str: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    # Argparse specific type field types
    argparse.FileType: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
                        'attr_kwargs': dict(GLOBAL_ATTR_KWARGS, **{
                            'value': None,
                            'required': {'callback': lambda x: x.required or x.default in (sys.stdout, sys.stdin)},
                            'upload': {'callback': is_upload}
                        })},

}


if six.PY2:
    TYPE_FIELDS.update({
        file: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
        unicode: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
              'attr_kwargs': GLOBAL_ATTR_KWARGS},
    })
elif six.PY3:
    import io
    TYPE_FIELDS.update({
        io.IOBase: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
    })



# There are cases where we can glean additional information about the form structure, e.g.
# a StoreAction with default=True can be different than a StoreTrueAction with default=False
ACTION_CLASS_TO_TYPE_FIELD = {
    argparse._StoreAction: update_dict_copy(TYPE_FIELDS, {}),
    argparse._StoreConstAction: update_dict_copy(TYPE_FIELDS, {}),
    argparse._StoreTrueAction: update_dict_copy(TYPE_FIELDS, {
        None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
               'attr_kwargs': update_dict_copy(GLOBAL_ATTR_KWARGS, {
                    'checked': {'callback': lambda x: x.default},
                    'value': None,
                    })
               },
    }),
    argparse._StoreFalseAction: update_dict_copy(TYPE_FIELDS, {
        None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
               'attr_kwargs': update_dict_copy(GLOBAL_ATTR_KWARGS, {
                    'checked': {'callback': lambda x: x.default},
                    'value': None,
                    })
               },
    })
}


class ArgParseNode(object):
    """
        This class takes an argument parser entry and assigns it to a Build spec
    """
    def __init__(self, action=None):
        fields = ACTION_CLASS_TO_TYPE_FIELD.get(type(action), TYPE_FIELDS)
        field_type = fields.get(action.type)
        if field_type is None:
            field_types = [i for i in fields.keys() if i is not None and issubclass(type(action.type), i)]
            if len(field_types) > 1:
                field_types = [i for i in fields.keys() if i is not None and isinstance(action.type, i)]
            if len(field_types) == 1:
                field_type = fields[field_types[0]]
        self.node_attrs = dict([(i, field_type[i]) for i in GLOBAL_ATTRS])
        null_check = field_type['nullcheck'](action)
        for attr, attr_dict in six.iteritems(field_type['attr_kwargs']):
            if attr_dict is None:
                continue
            if attr == 'value' and null_check:
                continue
            if 'action_name' in attr_dict:
                self.node_attrs[attr] = getattr(action, attr_dict['action_name'], None)
            elif 'callback' in attr_dict:
                self.node_attrs[attr] = attr_dict['callback'](action)

    @property
    def name(self):
        return self.node_attrs.get('name')

    def __str__(self):
        return json.dumps(self.node_attrs)

    def to_django(self):
        """
         This is a debug function to see what equivalent django models are being generated
        """
        exclude = {'name', 'model'}
        field_module = 'models'
        django_kwargs = {}
        if self.node_attrs['model'] == 'CharField':
            django_kwargs['max_length'] = 255
        django_kwargs['blank'] = not self.node_attrs['required']
        try:
            django_kwargs['default'] = self.node_attrs['value']
        except KeyError:
            pass
        return u'{0} = {1}.{2}({3})'.format(self.node_attrs['name'], field_module, self.node_attrs['model'],
                                           ', '.join(['{0}={1}'.format(i,v) for i,v in six.iteritems(django_kwargs)]),)



class ArgParseParser(BaseParser):

    def heuristic(self):
        return [
            self.script_ext in ['.py', '.py3', '.py2'],
            'argparse' in self.script_source,
            'ArgumentParser' in self.script_source,
            '.parse_args' in self.script_source,
            '.add_argument' in self.script_source,
        ]

    def extract_parser(self):
        parsers = []

        # Try exception-catching first; this should always work
        # Store prior to monkeypatch to restore
        parse_args_unmonkey = argparse.ArgumentParser.parse_args
        argparse.ArgumentParser.parse_args = parse_args_monkeypatch

        try:
            exec(self.script_source, {'argparse': argparse, '__name__': '__main__'})
        except ClintoArgumentParserException as e:
            # Catch the generated exception, passing the ArgumentParser object
            parsers.append(e.parser)
        except:
            sys.stderr.write('Error while trying exception-catch method on {0}:\n'.format(self.script_path))
            self.error = '{0}\n'.format(traceback.format_exc())
            sys.stderr.write(self.error)

        argparse.ArgumentParser.parse_args = parse_args_unmonkey

        if not parsers:
            try:
                module = imp.load_source('__name__', self.script_path)
            except:
                sys.stderr.write('Error while loading {0}:\n'.format(self.script_path))
                self.error = '{0}\n'.format(traceback.format_exc())
                sys.stderr.write(self.error)
            else:
                main_module = module.main.__globals__ if hasattr(module, 'main') else globals()
                parsers = [v for i, v in chain(six.iteritems(main_module), six.iteritems(vars(module)))
                           if issubclass(type(v), argparse.ArgumentParser)]
        if not parsers:
            f = tempfile.NamedTemporaryFile()
            try:
                ast_source = source_parser.parse_source_file(self.script_path)
                python_code = source_parser.convert_to_python(list(ast_source))
                f.write(six.b('\n'.join(python_code)))
                f.seek(0)
                module = imp.load_source('__main__', f.name)
            except:
                sys.stderr.write('Error while converting {0} to ast:\n'.format(self.script_path))
                self.error = '{0}\n'.format(traceback.format_exc())
                sys.stderr.write(self.error)
            else:
                main_module = module.main.__globals__ if hasattr(module, 'main') else globals()
                parsers = [v for i, v in chain(six.iteritems(main_module), six.iteritems(vars(module)))
                       if issubclass(type(v), argparse.ArgumentParser)]
        if not parsers:
            sys.stderr.write('Unable to identify ArgParser for {0}:\n'.format(self.script_path))
            return

        self.is_valid = True
        self.parser = parsers[0]

    def process_parser(self):
        self.class_name = os.path.splitext(os.path.basename(self.script_path))[0]
        self.script_path = self.script_path
        self.script_description = getattr(self.parser, 'description', None)
        self.script_groups = []
        self.nodes = OrderedDict()
        self.script_groups = []
        non_req = set([i.dest for i in self.parser._get_optional_actions()])
        self.optional_nodes = set([])
        self.containers = OrderedDict()
        for action in self.parser._actions:
            # This is the help message of argparse
            if action.default == argparse.SUPPRESS:
                continue
            node = ArgParseNode(action=action)
            container = action.container.title
            container_node = self.containers.get(container, None)
            if container_node is None:
                container_node = []
                self.containers[container] = container_node
            self.nodes[node.name] = node
            container_node.append(node.name)
            if action.dest in non_req:
                self.optional_nodes.add(node.name)

    def get_script_description(self):
        return {'name': self.class_name, 'path': self.script_path,
                'description': self.script_description,
                'inputs': [{'group': container_name, 'nodes': [self.nodes[node].node_attrs for node in nodes]}
                           for container_name, nodes in six.iteritems(self.containers)]}


