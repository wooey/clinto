try:
    import docopt

    DocoptExit = docopt.DocoptExit
except ImportError:
    DocoptExit = Exception

ParserExceptions = (DocoptExit, Exception)
