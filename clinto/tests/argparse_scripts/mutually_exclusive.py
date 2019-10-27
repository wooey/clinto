import argparse
import sys
import six

parser = argparse.ArgumentParser(description="Something")
group = parser.add_mutually_exclusive_group()
group.add_argument('--foo', action='store_true')
group.add_argument('--bar', action='store_false')
group2 = parser.add_mutually_exclusive_group()
group2.add_argument('--foo2', action='store_true')
group2.add_argument('--bar2', action='store_false')

if __name__ == '__main__':
    args = parser.parse_args()
    sys.stdout.write('{}'.format(args))
