import argparse
import re

def valid_date_type(arg_date):
    """
    Custom argparse *date* type for user dates values given from the command line
    """
    try:
        return re.search('([0-9]{8})', arg_date)
    except ValueError:
        msg = 'Given Date ({0}) not valid! Expected format, YYYYMMDD!'.format(arg_date_str)
        raise argparse.ArgumentTypeError(msg)

parser = argparse.ArgumentParser(description='Test parsing of a function type argument.')
parser.add_argument(
    'start_date',
    type=valid_date_type,
    help='Use date in format YYYYMMDD (e.g. 20180131)',
    default='20180131'
)
parser.add_argument(
    'lowercase',
    type=str.lower,
    help='Lowercase it',
    default='ABC',
)


def main():
    args = parser.parse_args()
    print(args.start_date)


if __name__ == '__main__':
    main()