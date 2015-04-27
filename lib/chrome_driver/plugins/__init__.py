#from pluginloader import *

def parse_all_plugins():
    import os
    import glob
    modules = glob.glob(os.path.dirname(__file__)+"/plugin_*.py")
    return [ os.path.basename(f)[:-3] for f in modules]

__all__ = parse_all_plugins()
for mod in __all__:
    __import__(mod, globals(), locals())