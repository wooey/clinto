from __future__ import absolute_import
import argparse
import sys
import six
import json
from itertools import chain
from .utils import expand_iterable, is_upload, update_dict_copy
from .base_parser import BaseParser

class ArgParseNode(object):
    """
        This class takes an argument parser entry and assigns it to a Build spec
    """
    def __init__(self, parameter=None, parent=None):
        self.parameter = parameter
        fields = parent.CLASS_TO_TYPE_FIELD.get(type(parameter), parent.TYPE_FIELDS)
        field_type = fields.get(parameter.type)
        if field_type is None:
            field_types = [i for i in fields.keys() if i is not None and issubclass(type(parameter.type), i)]
            if len(field_types) > 1:
                field_types = [i for i in fields.keys() if i is not None and isinstance(parameter.type, i)]
            if len(field_types) == 1:
                field_type = fields[field_types[0]]
        self.node_attrs = dict([(i, field_type[i]) for i in parent.GLOBAL_ATTRS])
        null_check = field_type['nullcheck'](parameter)
        for attr, attr_dict in six.iteritems(field_type['attr_kwargs']):
            if attr_dict is None:
                continue
            if attr == 'value' and null_check:
                continue
            if 'parameter_name' in attr_dict:
                self.node_attrs[attr] = getattr(parameter, attr_dict['parameter_name'])
            elif 'callback' in attr_dict:
                self.node_attrs[attr] = attr_dict['callback'](parameter)

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
                                           ', '.join(['{0}={1}'.format(i,v) for i,v in django_kwargs.iteritems()]),)

class ArgparseParser(BaseParser):
    def __init__(self, *args, **kwargs):
        super(ArgparseParser, self).__init__()
        self.CHOICE_LIMIT_MAP = {'?': '1', '+': '>=1', '*': '>=0'}

        self.GLOBAL_ATTR_KWARGS = {
            'name': {'parameter_name': 'dest'},
            'value': {'parameter_name': 'default'},
            'required': {'parameter_name': 'required'},
            'help': {'parameter_name': 'help'},
            'param': {'callback': lambda x: x.option_strings[0] if x.option_strings else ''},
            'choices': {'callback': lambda x: expand_iterable(x.choices)},
            'choice_limit': {'callback': lambda x: self.CHOICE_LIMIT_MAP.get(x.nargs, x.nargs)}
            }

        self.TYPE_FIELDS = {
            # Python Builtins
            bool: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
                   'attr_kwargs': self.GLOBAL_ATTR_KWARGS},
            float: {'model': 'FloatField', 'type': 'text', 'html5-type': 'number', 'nullcheck': lambda x: x.default is None,
                    'attr_kwargs': self.GLOBAL_ATTR_KWARGS},
            int: {'model': 'IntegerField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
                  'attr_kwargs': self.GLOBAL_ATTR_KWARGS},
            None: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
                  'attr_kwargs': self.GLOBAL_ATTR_KWARGS},
            str: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
                  'attr_kwargs': self.GLOBAL_ATTR_KWARGS},

            # argparse Types
            argparse.FileType: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
                                'attr_kwargs': dict(self.GLOBAL_ATTR_KWARGS, **{
                                    'value': None,
                                    'required': {'callback': lambda x: x.required or x.default in (sys.stdout, sys.stdin)},
                                    'upload': {'callback': is_upload}
                                })},
        }

        if six.PY2:
            self.TYPE_FIELDS.update({
                file: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
                   'attr_kwargs': self.GLOBAL_ATTR_KWARGS},
                unicode: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
                      'attr_kwargs': self.GLOBAL_ATTR_KWARGS},
            })
        elif six.PY3:
            import io
            self.TYPE_FIELDS.update({
                io.IOBase: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
                   'attr_kwargs': self.GLOBAL_ATTR_KWARGS},
            })

        self.CLASS_TO_TYPE_FIELD = {
            argparse._StoreAction: update_dict_copy(self.TYPE_FIELDS, {}),
            argparse._StoreConstAction: update_dict_copy(self.TYPE_FIELDS, {}),
            argparse._StoreTrueAction: update_dict_copy(self.TYPE_FIELDS, {
                None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
                       'attr_kwargs': update_dict_copy(self.GLOBAL_ATTR_KWARGS, {
                            'checked': {'callback': lambda x: x.default},
                            'value': None,
                            })
                       },
            }),
            argparse._StoreFalseAction: update_dict_copy(self.TYPE_FIELDS, {
                None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
                       'attr_kwargs': update_dict_copy(self.GLOBAL_ATTR_KWARGS, {
                            'checked': {'callback': lambda x: x.default},
                            'value': None,
                            })
                       },
            })
        }

    def get_parsers(self, module, globals_dict=None):
        super(ArgparseParser, self).get_parsers(module, globals_dict=globals_dict)
        main_method = module.main.__globals__ if hasattr(module, 'main') else globals_dict
        return [v for i, v in chain(six.iteritems(main_method), six.iteritems(vars(module)))
                   if issubclass(type(v), argparse.ArgumentParser)]

    def get_script_description(self, parser):
        return getattr(parser, 'description', None)

    def get_optional_parameters(self, parser):
        return parser._get_optional_actions()

    def get_parameters(self, parser):
        # argparse.SUPPRESS is the help message of argparse
        return [action for action in parser._actions if action.default != argparse.SUPPRESS]

    def get_parameter_node(self, parameter=None):
        return ArgParseNode(parent=self, parameter=parameter)

    def get_parameter_group(self, parameter=None):
        return parameter.container.title