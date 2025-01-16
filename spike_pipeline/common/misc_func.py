import sys
from importlib import reload


def reload_module(module_name, *names):
    '''

    :param module_name:
    :param names:
    :return:
    '''

    if module_name in sys.modules:
        reload(sys.modules[module_name])
    else:
        __import__(module_name, fromlist=names)

    for name in names:
        globals()[name] = getattr(sys.modules[module_name], name)