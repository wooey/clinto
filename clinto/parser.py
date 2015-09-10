from .parsers import ArgParseParser

parsers = [
    ArgParseParser,

]


class Parser(object):

    def __init__(self, script_path=None):
        self.parser = None

        # Load file
        with open(script_path, 'r') as f:
            script_source = f.read()

        for pc in parsers:
            parser = pc(script_path, script_source)
            if parser.is_valid:
                # It worked
                self.parser = parser

    def get_script_description(self):
        if self.parser:
            return self.parser.get_script_description()

    @property
    def json(self):
        if self.parser:
            return self.parser.json
