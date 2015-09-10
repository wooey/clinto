from __future__ import absolute_import
import json
import os
import copy


def update_dict_copy(a, b):
    temp = copy.deepcopy(a)
    temp.update(b)
    return temp


class ClintoArgumentParserException(Exception):
    def __init__(self, parser, *args, **kwargs):
        self.parser = parser


def parse_args_monkeypatch(self, *args, **kwargs):
    raise ClintoArgumentParserException(self)


class BaseParser(object):

    extensions = []
    contains = ""

    def __init__(self, script_path=None, script_source=None):
        self.is_valid = False
        self.error = ''
        self.parser = None

        self.script_path = script_path
        self.script_source = script_source

        if not self.check_valid():
            return

        self.extract_parser()

        if self.parser is None:
            return

        self.process_parser()

    def check_valid(self):
        ext = os.path.splitext(os.path.basename(self.script_path))[1]
        return ext in self.extensions and self.contains in self.script_source

    def extract_parser(self):
        pass

    def process_parser(self):
        pass

    def get_script_description(self):
        pass

    @property
    def json(self):
        return json.dumps(self.get_script_description())
