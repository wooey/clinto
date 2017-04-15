import sys

from distutils.version import StrictVersion

PY_FULL_VERSION = StrictVersion('{}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
PY_MINOR_VERSION = StrictVersion('{}.{}'.format(sys.version_info.major, sys.version_info.minor))
PY36 = StrictVersion('3.6')
