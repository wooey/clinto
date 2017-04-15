import os
import unittest

from . import factories
from clinto.version import PY_MINOR_VERSION, PY36
from clinto.parsers.argparse_ import ArgParseNode, expand_iterable, ArgParseParser
from clinto.parser import Parser


class Test_ArgParse(unittest.TestCase):
    def setUp(self):
        self.parser = factories.ArgParseFactory()
        def test_func(fields, defs):
            for i in self.parser.COMMON:
                assert fields[i] == defs[i], "{}: {} is not {}\n".format(i, fields[i], defs[i])
        self.base_test = test_func
        self.base_dir = os.path.split(__file__)[0]
        self.parser_script_dir = 'argparse_scripts'
        self.script_dir = os.path.join(self.base_dir, self.parser_script_dir)

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
            script_params['inputs'][0],
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


suite = unittest.TestLoader().loadTestsFromTestCase(Test_ArgParse)
unittest.TextTestRunner(verbosity=2).run(suite)
