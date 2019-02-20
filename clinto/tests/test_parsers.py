import os
import unittest

import six
from . import factories
from clinto.version import PY_MINOR_VERSION, PY36
from clinto.parsers.argparse_ import ArgParseNode, expand_iterable, ArgParseParser
from clinto.parsers.constants import SPECIFY_EVERY_PARAM
from clinto.parser import Parser


class TestArgParse(unittest.TestCase):
    def setUp(self):
        self.parser = factories.ArgParseFactory()
        def test_func(fields, defs):
            for i in self.parser.COMMON:
                assert fields[i] == defs[i], "{}: {} is not {}\n".format(i, fields[i], defs[i])
        self.base_test = test_func
        self.base_dir = os.path.split(__file__)[0]
        self.parser_script_dir = 'argparse_scripts'
        self.script_dir = os.path.join(self.base_dir, self.parser_script_dir)

    def test_subparser(self):
        script_path = os.path.join(self.script_dir, 'subparser_script.py')
        parser = Parser(script_path=script_path)
        description = parser.get_script_description()
        main_parser = description['inputs']['']
        main_parser_group1 = main_parser[0]
        self.assertEqual(main_parser_group1['nodes'][0]['name'], 'test_arg')
        self.assertEqual(main_parser_group1['group'], 'optional arguments')

        subparser1 = description['inputs']['subparser1']
        subparser_group1 = subparser1[0]
        self.assertEqual(subparser_group1['nodes'][0]['name'], 'sp1')

    def test_script_version(self):
        script_path = os.path.join(self.script_dir, 'choices.py')
        parser = Parser(script_path=script_path)
        description = parser.get_script_description()
        self.assertEqual(description['version'], '2' if six.PY2 else '3')

    def test_file_field(self):
        filefield = ArgParseNode(action=self.parser.filefield)
        attrs = filefield.node_attrs
        self.base_test(attrs, self.parser.FILEFIELD)
        assert attrs['upload'] is False
        assert attrs['model'] == 'FileField'

    def test_upload_file_field(self):
        upload = ArgParseNode(action=self.parser.uploadfield)
        attrs = upload.node_attrs
        self.base_test(attrs, self.parser.UPLOADFILEFIELD)
        assert attrs['upload'] is True
        assert attrs['model'] == 'FileField'

    def test_choice_field(self):
        choicefield = ArgParseNode(action=self.parser.choicefield)
        attrs = choicefield.node_attrs
        self.base_test(attrs, self.parser.CHOICEFIELD)
        assert attrs['model'] == 'CharField'
        # test range
        rangefield = ArgParseNode(action=self.parser.rangefield)
        assert rangefield.node_attrs['choices'] == expand_iterable(self.parser.rangefield.choices)

    def test_argparse_script(self):
        script_path = os.path.join(self.script_dir, 'choices.py')
        parser = Parser(script_path=script_path)

        script_params = parser.get_script_description()
        self.assertEqual(script_params['path'], script_path)

        # Make sure we return parameters in the order the script defined them and in groups
        # We do not test this that exhaustively atm since the structure is likely to change when subparsers
        # are added
        self.assertDictEqual(
            script_params['inputs'][''][0],
            {
                'nodes': [
                    {'param_action': set([]), 'name': 'first_pos', 'required': True, 'param': '', 'choices': None,
                    'choice_limit': None, 'model': 'CharField', 'type': 'text', 'help': None},
                    {'param_action': set([]), 'name': 'second-pos', 'required': True, 'param': '', 'choices': None,
                    'choice_limit': None, 'model': 'CharField', 'type': 'text', 'help': None}
                ],
                'group': 'positional arguments'
            }
        )

    def test_argparse_specify_every_param(self):
        script_path = os.path.join(self.script_dir, 'choices.py')
        parser = Parser(script_path=script_path)

        script_params = parser.get_script_description()
        self.assertEqual(script_params['path'], script_path)

        append_field = [i for i in script_params['inputs'][''][1]['nodes'] if i['param'] == '--need-at-least-one-numbers'][0]
        self.assertIn(SPECIFY_EVERY_PARAM, append_field['param_action'])

    def test_function_type_script(self):
        script_path = os.path.join(self.script_dir, 'function_argtype.py')
        parser = Parser(script_path=script_path)

        script_params = parser.get_script_description()
        self.assertEqual(script_params['path'], script_path)

        self.assertDictEqual(
            script_params['inputs'][''][0],
            {
                'nodes': [
                    {
                        'param_action': set([]),
                        'name': 'start_date',
                        'required': True,
                        'param': '',
                        'choices': None,
                        'choice_limit': None,
                        'model': 'CharField',
                        'type': 'text',
                        'help': 'Use date in format YYYYMMDD (e.g. 20180131)',
                        # The default argument
                        'value': '20180131'
                    },
                    {
                        'param_action': set([]),
                        'name': 'lowercase',
                        'required': True,
                        'param': '',
                        'choices': None,
                        'value': 'ABC',
                        'choice_limit': None,
                        'model': 'CharField',
                        'type': 'text',
                        'help': 'Lowercase it'
                    }

                ],
                'group': 'positional arguments'
            }
        )

    def test_error_script(self):
        script_path = os.path.join(self.script_dir, 'error_script.py')
        parser = Parser(script_path=script_path)

        if PY_MINOR_VERSION >= PY36:
            self.assertIn('ModuleNotFoundError', parser.error)
        else:
            self.assertIn('ImportError', parser.error)
        self.assertIn('something_i_dont_have', parser.error)

        script_path = os.path.join(self.script_dir, 'choices.py')
        parser = Parser(script_path=script_path)
        self.assertEquals('', parser.error)

    def test_zipapp(self):
        script_path = os.path.join(self.script_dir, 'data_reader.zip')
        parser = Parser(script_path=script_path)
        script_params = parser.get_script_description()
        self.assertDictEqual(
            script_params['inputs'][''][0],
            {
                'nodes': [
                    {'param_action': set([]), 'name': 'n', 'required': False, 'param': '-n', 'choices': None, 'value': -1,
                    'choice_limit': None, 'model': 'IntegerField', 'type': 'text', 'help': 'The number of rows to read.'}],
                'group': 'optional arguments',
            }
        )


class TestDocOpt(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.split(__file__)[0]
        self.parser_script_dir = 'docopt_scripts'
        self.script_dir = os.path.join(self.base_dir, self.parser_script_dir)

    def test_naval_fate(self):
        script_path = os.path.join(self.script_dir, 'naval_fate.py')
        parser = Parser(script_path=script_path)
        script_params = parser.get_script_description()
        self.assertEqual(script_params['path'], script_path)
        self.assertEqual(script_params['name'], 'naval_fate')

        # Make sure we return parameters in the order the script defined them and in groups
        # We do not test this that exhaustively atm since the structure is likely to change when subparsers
        # are added
        self.assertDictEqual(
            script_params['inputs'][''][0],
            {
                'nodes': [
                    {'model': 'CharField', 'type': 'text', 'name': 'speed', 'param': '--speed'},
                    {'model': 'BooleanField', 'type': 'checkbox', 'name': 'moored', 'param': '--moored'},
                    {'model': 'BooleanField', 'type': 'checkbox', 'name': 'drifting', 'param': '--drifting'}
                ],
                'group': 'default'
            }
        )


if __name__ == '__main__':
    unittest.main()
