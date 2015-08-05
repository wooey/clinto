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

class BaseParser(object):
    # the choice limit map should return strings:
    #  '1' if there is only one choice available,
    # '>=1' if there needs to be at least 1 choice.
    # '>=0' if there needs to be at least 0 choices (it's optional, but accepts multiple).
    CHOICE_LIMIT_MAP = {}

    # We want to map the parser's argument type to model fields for the ORM as well as html input types
    # This variable corresponds to the output that defines:
    GLOBAL_ATTRS = [
        'model', # the model type the action/command is mapping to,
        'type' # the HTML input type the action/command is mapping to
    ]

    # This is where the real work happens. This interacts with the actual commands/actions of the parser.
    # We use this to map the action/command attributes to its related html input type. It is a dict
    # of the form: {'name_for_html_input': {
    # and either one or both of:
    #  'action_name': 'attribute_name_on_action', 'callback': 'function_to_evaluate_action_and_return_value'} }

    GLOBAL_ATTR_KWARGS = {
        'name': {},
        'value': {},
        'required': {},
        'help': {},
        'param': {},
        'choices': {},
        'choice_limit': {}
    }

    # Currently, the supported parsers convert arguments to known variable types, as defined in __builtins__
    TYPE_FIELDS = {
        # Python Builtins
        # an example
        # bool: {
        #     'model': 'BooleanField',
        #     'type': 'checkbox', # the HTML input type
        #     'nullcheck': lambda x: x.default is None, # nullcheck is a function to determine if the default value is empty. This handles cases for cases like default=False for boolean which are actually not null but a simple 'if x' would fail
        #     'attr_kwargs': GLOBAL_ATTR_KWARGS # the dictionary storing how to extract other fields from the parser
        # },
        bool: {},
        float: {},
        int: {},
        None: {},
        str: {},

        # specific types to the parser should be added here as well, such a this:
        # argparse Types
        # argparse.FileType: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
        #                     'attr_kwargs': dict(GLOBAL_ATTR_KWARGS, **{
        #                         'value': None,
        #                         'required': {'callback': lambda x: x.required or x.default in (sys.stdout, sys.stdin)},
        #                         'upload': {'callback': is_upload}
        #                     })},
    }

    if six.PY2:
        TYPE_FIELDS.update({
            file: {},
            unicode: {},
        })
    elif six.PY3:
        import io
        TYPE_FIELDS.update({
            io.IOBase: {},
        })

    # There are cases where we can glean additional information about the form structure, e.g.
    # a StoreAction with default=True can be different than a StoreTrueAction with default=False
    CLASS_TO_TYPE_FIELD = {
    }

    def get_parsers(self, module, globals_dict=None):
        if globals_dict is None:
            globals_dict = globals()

    def get_script_description(self, parser):
        raise NotImplementedError

    def get_optional_parameters(self, parser):
        raise NotImplementedError

    def get_parameters(self, parser):
        raise NotImplementedError