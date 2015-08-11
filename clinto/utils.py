#TODO: Move this stuff to a utils file
def is_upload(action):
    """Checks if this should be a user upload

    :param action:
    :return: True if this is a file we intend to upload from the user
    """
    return 'r' in action.type._mode and (action.default is None or
                                         getattr(action.default, 'name') not in (sys.stderr.name, sys.stdout.name))

def expand_iterable(choices):
    """
    Expands an iterable into a list. We use this to expand generators/etc.
    """
    return [i for i in choices] if hasattr(choices, '__iter__') else None