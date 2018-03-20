'''
    Build python extensions on-the-fly.
'''

from .core import compile_module, module_from_source
from . import utils

__all__ = ['compile_module', 'module_from_source', 'utils']
__version__ = '0.9.4'
