import unittest, sys
from . import factories
from ..parser import ArgParseNode, Parser, expand_iterable

class Test_ArgParse(unittest.TestCase):
    def setUp(self):
        self.parser = factories.ArgParseFactory()
        def test_func(fields, defs):
            for i in self.parser.COMMON:
                assert fields[i] == defs[i], "{}: {} is not {}\n".format(i, fields[i], defs[i])
        self.base_test = test_func

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
        nodes = Parser(parsers=[self.parser.parser])


suite = unittest.TestLoader().loadTestsFromTestCase(Test_ArgParse)
unittest.TextTestRunner(verbosity=2).run(suite)