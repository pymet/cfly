import unittest

from cfly import compile_module

class TestCase(unittest.TestCase):
    def test_compile(self):
        mymod = compile_module('mymod', '#include <Python.h>')


if __name__ == '__main__':
    unittest.main()
