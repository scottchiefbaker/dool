"""Load the dool script (which has no .py extension) as a module."""
import importlib.machinery
import importlib.util
import os

DOOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dool')


def load_dool():
    loader = importlib.machinery.SourceFileLoader('dool_under_test', DOOL_PATH)
    spec = importlib.util.spec_from_loader('dool_under_test', loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


dool = load_dool()
