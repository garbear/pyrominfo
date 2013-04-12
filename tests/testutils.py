# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

def loadModule(mod):
    """
    This will first try to load the specified module from the pyrominfo package
    using the current module search path. If it can't be found, then the parent
    directory is added to the module search path and the import attempt is
    repeated.
    """
    try:
        # from pyrominfo import gameboy, etc
        pyrominfo = __import__("pyrominfo", globals(), locals(), [mod])
    except ImportError:
        import os
        parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.sys.path.insert(0, parentdir)
        pyrominfo = __import__("pyrominfo", globals(), locals(), [mod])

    try:
        return getattr(pyrominfo, mod)
    except AttributeError:
        raise ImportError("testutils.loadModule() can't find module %s in pyrominfo package" % mod)
