from .parsers import ArgParseParser, DocOptParser

parsers = [
    ArgParseParser,
    DocOptParser,
]


class Parser(object):

    def __init__(self, script_path=None, script_name=None):
        self.parser = None

        # Load file
        with open(script_path, 'r') as f:
            script_source = f.read()

        parser_obj = [pc(script_path, script_source) for pc in parsers]
        parser_obj = sorted(parser_obj, key=lambda x: x.score, reverse=True)

        for po in parser_obj:
            if po.is_valid:
                # It worked
                self.parser = po

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
        return ''
