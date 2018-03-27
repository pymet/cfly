import unittest

from cfly import build_module


class TestCase(unittest.TestCase):
    def test_compile(self):
        build_module('mymod')


if __name__ == '__main__':
    unittest.main()
