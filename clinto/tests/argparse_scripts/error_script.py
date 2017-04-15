import argparse
import something_i_dont_have

parser = argparse.ArgumentParser(description="Something")

if __name__ == '__main__':
    args = parser.parse_args()
    sys.stdout.write('{}'.format(args))
