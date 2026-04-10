import argparse
import sys
import something_i_dont_have  # noqa: F401

parser = argparse.ArgumentParser(description="Something")
parser.add_argument("-foo")

if __name__ == "__main__":
    args = parser.parse_args()
    sys.stdout.write("{}".format(args))
