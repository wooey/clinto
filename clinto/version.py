import sys

# Use tuples for version comparisons so this module works on Python 3.12+,
# where distutils was removed from the standard library.
PY_FULL_VERSION = (
    sys.version_info.major,
    sys.version_info.minor,
    sys.version_info.micro,
)
PY_MINOR_VERSION = (sys.version_info.major, sys.version_info.minor)
PY36 = (3, 6)
