from __future__ import absolute_import

import sys
import os
import json
import imp
import inspect
import tempfile
import traceback
import six
from collections import OrderedDict
from itertools import chain
from ..ast import source_parser
from ..utils import is_upload, expand_iterable
from .base import BaseParser, parse_args_monkeypatch, ClintoArgumentParserException, update_dict_copy

try:
    import docopt
except ImportError:
    docopt = None


GLOBAL_ATTRS = ['model', 'type']


GLOBAL_ATTR_KWARGS = {
    'name': {'action_name': 'dest'},
    'value': {'action_name': 'default'},
    'required': {'action_name': 'required'},
    'help': {'action_name': 'help'},
    }

TYPE_FIELDS = {
    # Python Builtins
    bool: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.value is None,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
    float: {'model': 'FloatField', 'type': 'text', 'html5-type': 'number', 'nullcheck': lambda x: x.value is None,
            'attr_kwargs': GLOBAL_ATTR_KWARGS},
    int: {'model': 'IntegerField', 'type': 'text', 'nullcheck': lambda x: x.value is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    None: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.value is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    str: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.value == '' or x.value is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
}



class DocOptNode(object):
    """
        This class takes an argument parser entry and assigns it to a Build spec
    """
    def __init__(self, name, option=None):
        field_type = TYPE_FIELDS.get(option.type)
        if field_type is None:
            field_types = [i for i in fields.keys() if i is not None and issubclass(type(option.type), i)]
            if len(field_types) > 1:
                field_types = [i for i in fields.keys() if i is not None and isinstance(option.type, i)]
            if len(field_types) == 1:
                field_type = fields[field_types[0]]
        self.node_attrs = dict([(i, field_type[i]) for i in GLOBAL_ATTRS])
        self.node_attrs['name'] = name
        self.node_attrs['param'] = option.long if option.long else option.short

    @property
    def name(self):
        return self.node_attrs.get('name')

    def __str__(self):
        return json.dumps(self.node_attrs)


class DocOptParser(BaseParser):

    def heuristic(self):
        return [
            self.script_ext in ['.py', '.py3', '.py2'],
            'docopt' in self.script_source,
            '__doc__' in self.script_source,
        ]

    def extract_parser(self):
        if docopt is None:
            return False

        try:
            module = imp.load_source('__name__', self.script_path)

        except Exception:
            sys.stderr.write('Error while loading {0}:\n'.format(self.script_path))
            self.error = '{0}\n'.format(traceback.format_exc())
            sys.stderr.write(self.error)
            return

        try:
            doc = module.__doc__

        except AttributeError:
            return

        if doc is None:
            return

        # We have the documentation string in 'doc'
        self.is_valid = True
        self.parser = doc

    def process_parser(self):
        """
        We can't use the exception catch trick for docopt because the module prevents access to
        it's innards __all__ = ['docopt']. Instead call with --help enforced, catch sys.exit and
        work up to the calling docopt function to pull out the elements. This is horrible.

        :return:
        """

        try:
            # Parse with --help to enforce exit
            usage_sections = docopt.docopt(self.parser, ['--help'])
        except SystemExit as e:
            parser = inspect.trace()[-2][0].f_locals

        '''
        docopt represents all values as strings and doesn't automatically cast, we probably want to do
        some testing to see if we can convert the default value (Option.value) to a particular type.
        '''

        def guess_type(s):
            try:
                v = float(s)
                v = int(s)
                v = s
            except ValueError:
                pass

            return type(v)

        self.script_groups = ['Arguments']
        self.nodes = OrderedDict()
        self.containers = OrderedDict()
        self.containers['default'] = []

        for option in parser['options']:
            if option.long in ['--help', '--version']:
                continue

            option.type = guess_type(option.value)
            option_name = option.long.strip('-')
            node = DocOptNode(option_name, option=option)

            self.nodes[option_name] = node
            self.containers['default'].append(option_name)

        self.class_name = os.path.splitext(os.path.basename(self.script_path))[0]
        self.script_path = self.script_path
        self.script_description = self.parser

    def get_script_description(self):
        return {'name': self.class_name, 'path': self.script_path,
                'description': self.script_description,
                'inputs': [{'group': container_name, 'nodes': [self.nodes[node].node_attrs for node in nodes]}
                           for container_name, nodes in six.iteritems(self.containers)]}


