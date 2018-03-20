'''
    Build python extensions on-the-fly.
'''

from .core import compile_module, module_from_source

__all__ = ['compile_module', 'module_from_source']
__version__ = '0.9.4'
