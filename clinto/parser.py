from __future__ import absolute_import
import sys
import json
import imp
import traceback
import tempfile
import six
import copy
import types
from collections import OrderedDict
from .ast import source_parser
from itertools import chain
from .utils import expand_iterable, is_upload
from . import argparse_parser, click_parser

class ParserNode(object):
    """
    This class takes an argument parser entry and assigns it to a Build spec
    :keyword action: The click command/argparse action/whatever parser command group we are looking at
    """
    def __init__(self, action=None):
        # ACTION_CLASS_TO_TYPE_FIELD is
        fields = CLASS_TO_TYPE_FIELD.get(type(action), TYPE_FIELDS)
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
                self.node_attrs[attr] = getattr(action, attr_dict['action_name'])
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

SUPPORTED_PARSERS = {
    'argparse': {
        'methods': ['__package__', 'ArgumentParser'],
        'parser': argparse_parser.ArgparseParser,
    },
    'click': {
        'methods': ['__package__', 'parser', 'ClickException'],
        'parser': click_parser#.ClickParser,
    },
}


class Parser(object):
    def __init__(self, script_path=None, script_name=None, parsers=None):
        self.valid = False
        self.error = ''
        parser_lib = None
        if parsers is None:
            try:
                module = imp.load_source(script_name, script_path)
            except:
                sys.stderr.write('Error while loading {0}:\n'.format(script_path))
                self.error = '{0}\n'.format(traceback.format_exc())
                sys.stderr.write(self.error)
                try:
                    f = tempfile.NamedTemporaryFile()
                    ast_source = source_parser.parse_source_file(script_path)
                    python_code = source_parser.convert_to_python(list(ast_source))
                    f.write(six.b('\n'.join(python_code)))
                    f.seek(0)
                    module = imp.load_source(script_name, f.name)
                except:
                    sys.stderr.write('Error while converting {0} to ast:\n'.format(script_path))
                    self.error = '{0}\n'.format(traceback.format_exc())
                    sys.stderr.write(self.error)
                    sys.stderr.write('Unable to identify ArgParser for {0}:\n'.format(script_path))
                    return
            # figure out what type of parser the script is using
            # get our imports
            module_imports = set(dir(module)).intersection(sys.modules.keys())
            # figure out what parser is being used by duck-typing
            for i in module_imports:
                if i not in SUPPORTED_PARSERS:
                    continue
                potential_parser = getattr(module, i, None)
                if potential_parser is None:
                    continue
                if not any(getattr(potential_parser, method, False) is False for method in SUPPORTED_PARSERS.get(i, {}).get('methods', [])):
                    parser_lib = SUPPORTED_PARSERS[i]['parser']()
                    break
        if parser_lib is None:
            self.error = 'Unable to identify parser for {0}:\n'.format(script_path)
            sys.stderr.write(self.error)
            return
        available_parsers = parser_lib.get_parsers(module, globals_dict=globals())
        if not available_parsers:
            self.error = 'Unable to identify {} parser for {}:\n'.format(i, script_path)
            sys.stderr.write(self.error)
            return

        self.valid = True
        parser = available_parsers[0]
        self.class_name = script_name
        self.script_path = script_path
        self.script_description = parser_lib.get_script_description(parser)
        self.script_groups = []
        self.parameter_nodes = OrderedDict()
        self.script_groups = []
        non_req = set([i.dest for i in parser_lib.get_optional_parameters(parser)])
        self.optional_parameters = set([])
        self.parameter_groups = OrderedDict()
        for parameter in parser_lib.get_parameters(parser):
            parameter_node = parser_lib.get_parameter_node(parameter=parameter)
            parameter_group = parser_lib.get_parameter_group(parameter=parameter)

            parameter_group_node = self.parameter_groups.get(parameter_group, None)
            if parameter_group_node is None:
                parameter_group_node = []
                self.parameter_groups[parameter_group] = parameter_group_node

            self.parameter_nodes[parameter_node.name] = parameter_node
            parameter_group_node.append(parameter_node.name)
            if parameter_node.parameter in non_req:
                self.optional_parameters.add(parameter_node.name)

    def get_script_description(self):
        return {'name': self.class_name, 'path': self.script_path,
                'description': self.script_description,
                'inputs': [{'group': group_name, 'nodes': [self.parameter_nodes[node].node_attrs for node in group_nodes]}
                           for group_name, group_nodes in six.iteritems(self.parameter_groups)]}

    @property
    def json(self):
        return json.dumps(self.get_script_description())
