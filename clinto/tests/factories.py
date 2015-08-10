import argparse
import six
try:
    import xrange
except ImportError:
    xrange = six.moves.range

param_int = 0

class BaseDict(dict):
    def __init__(self, **kwargs):
        super(BaseDict, self).__init__()
        global param_int
        base_dict = {
            'param': '--test-param{}'.format(param_int),
            'required': False,
        }
        param_int = param_int+1
        base_dict.update(**kwargs)
        self.update(**base_dict)

class ArgParseFactory(object):
    DESCRIPTION = 'ArgParse Factory'
    COMMON = ['param', 'required']
    BASEFIELD = BaseDict()
    FILEFIELD = BaseDict(param='--ff-out', type=argparse.FileType('w'), help='Test help')
    UPLOADFILEFIELD = BaseDict(type=argparse.FileType('r'))
    CHOICEFIELD = BaseDict(choices=['a', 'b', 'c'])
    RANGECHOICES = BaseDict(choices=xrange(-10,20,2))

    def __init__(self):
        super(ArgParseFactory, self).__init__()
        self.parser = argparse.ArgumentParser(description=self.DESCRIPTION)
        self.filefield = self.parser.add_argument(self.FILEFIELD['param'], help=self.FILEFIELD['help'],
                                                  type=self.FILEFIELD['type'])
        self.uploadfield = self.parser.add_argument(self.UPLOADFILEFIELD['param'], type=self.UPLOADFILEFIELD['type'])
        self.choicefield = self.parser.add_argument(self.CHOICEFIELD['param'], choices=self.CHOICEFIELD['choices'])
        self.rangefield = self.parser.add_argument(self.RANGECHOICES['param'], choices=self.RANGECHOICES['choices'])