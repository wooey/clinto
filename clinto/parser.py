import zipfile

from .parsers import ArgParseParser, DocOptParser

parsers = [
    ArgParseParser,
    DocOptParser,
]


class Parser(object):

    def __init__(self, script_path=None, script_name=None):
        self.parser = None
        self._error = ''

        if zipfile.is_zipfile(script_path):
            with zipfile.ZipFile(script_path) as zip:
                with zip.open('__main__.py', 'r') as f:
                    script_source = f.read().decode('utf-8')
        else:
            with open(script_path, 'r') as f:
                script_source = f.read()

        parser_obj = [pc(script_path=script_path, script_source=script_source) for pc in parsers]
        parser_obj = sorted(parser_obj, key=lambda x: x.score, reverse=True)

        for po in parser_obj:
            if po.is_valid:
                # It worked
                self.parser = po
                break
        else:
            # No parser found, fetch the error from the highest scoring parser for reporting
            self._error = parser_obj[0].error



    def get_script_description(self):
        if self.parser:
            return self.parser.get_script_description()

    @property
    def json(self):
        if self.parser:
            return self.parser.json
        return {}

    @property
    def valid(self):
        if self.parser:
            return self.parser.is_valid
        return False

    @property
    def error(self):
        if self.parser:
            return self.parser.error
        return self._error
