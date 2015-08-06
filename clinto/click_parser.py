from __future__ import absolute_import
from click.core import Command
import sys
import six
from itertools import chain
from .utils import expand_iterable, is_upload, update_dict_copy
from .base_parser import BaseParser

class ArgparseParser(BaseParser):
    def __init__(self, *args, **kwargs):
        super(ArgparseParser, self).__init__(*args, **kwargs)
        self.CHOICE_LIMIT_MAP = {'?': '1', '+': '>=1', '*': '>=0'}

        self.GLOBAL_ATTR_KWARGS = {
            'name': {'action_name': 'dest'},
            'value': {'action_name': 'default'},
            'required': {'action_name': 'required'},
            'help': {'action_name': 'help'},
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
            # argparse._StoreAction: update_dict_copy(self.TYPE_FIELDS, {}),
            # argparse._StoreConstAction: update_dict_copy(self.TYPE_FIELDS, {}),
            # argparse._StoreTrueAction: update_dict_copy(self.TYPE_FIELDS, {
            #     None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
            #            'attr_kwargs': update_dict_copy(self.GLOBAL_ATTR_KWARGS, {
            #                 'checked': {'callback': lambda x: x.default},
            #                 'value': None,
            #                 })
            #            },
            # }),
            # argparse._StoreFalseAction: update_dict_copy(self.TYPE_FIELDS, {
            #     None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
            #            'attr_kwargs': update_dict_copy(self.GLOBAL_ATTR_KWARGS, {
            #                 'checked': {'callback': lambda x: x.default},
            #                 'value': None,
            #                 })
            #            },
            # })
        }

    def get_parsers(self, module, globals_dict=None, *args, **kwargs):
        super(ArgparseParser, self).get_parsers(*args, **kwargs)
        main_method = module.main.__globals__ if hasattr(module, 'main') else globals
        return [v for i, v in chain(six.iteritems(main_method), six.iteritems(vars(module)))
                   if issubclass(type(v), Command)]