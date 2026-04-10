from __future__ import absolute_import
import copy
import importlib.machinery
import importlib.util
import json
import os
import sys
from contextlib import contextmanager


def update_dict_copy(a, b):
    temp = copy.deepcopy(a)
    temp.update(b)
    return temp


@contextmanager
def inserted_sys_path(path):
    if path:
        sys.path.insert(0, path)
        yield
        sys.path.pop(0)


class ClintoArgumentParserException(Exception):
    def __init__(self, parser, *args, **kwargs):
        self.parser = parser


def parse_args_monkeypatch(self, *args, **kwargs):
    raise ClintoArgumentParserException(self)


def load_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        loader = importlib.machinery.SourceFileLoader(module_name, path)
        spec = importlib.util.spec_from_loader(module_name, loader)

    if spec is None or spec.loader is None:
        raise ImportError(
            "Unable to load module {0} from {1}".format(module_name, path)
        )

    module = importlib.util.module_from_spec(spec)
    previous_module = sys.modules.get(module_name)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception:
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module
        raise

    if previous_module is None:
        sys.modules.pop(module_name, None)
    else:
        sys.modules[module_name] = previous_module

    return module


class BaseParser(object):
    def __init__(self, script_path=None, script_source=None, ignore_bad_imports=False):
        self.is_valid = False
        self.error = ""
        self.parser = None
        self.ignore_bad_imports = ignore_bad_imports

        self.script_path = script_path
        # We need this for heuristic, may as well happen once
        if self.script_path:
            self.script_ext = os.path.splitext(os.path.basename(self.script_path))[1]

        self.script_source = script_source

        self._heuristic_score = None

        with inserted_sys_path(
            os.path.dirname(self.script_path) if self.script_path else None
        ):
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
