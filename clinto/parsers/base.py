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

    def __init__(self, script_path=None, script_source=None):
        self.is_valid = False
        self.error = ''
        self.parser = None

        self.script_path = script_path
        # We need this for heuristic, may as well happen once
        if self.script_path:
            self.script_ext = os.path.splitext(os.path.basename(self.script_path))[1]

        self.script_source = script_source

        self._heuristic_score = None

        self.extract_parser()

        if self.parser is None:
            return

        self.process_parser()

    @property
    def score(self):
        """
        Calculate and return a heuristic score for this Parser against the provided
        script source and path. This is used to order the ArgumentParsers as "most likely to work"
        against a given script/source file.

        Each parser has a calculate_score() function that returns a list of booleans representing
        the matches against conditions. This is converted into a % match and used to sort parse engines.

        :return: float
        """
        if self._heuristic_score is None:
            matches = self.heuristic()
            self._heuristic_score = float(sum(matches)) / float(len(matches))
        return self._heuristic_score

    def extract_parser(self):
        pass

    def process_parser(self):
        pass

    def get_script_description(self):
        return {}

    @property
    def json(self):
        return json.dumps(self.get_script_description())
