# from cfly.core import parse_source
# import sys

# print(parse_source('''
# #include <Python.h>
# struct Foo {
#     PyObject_HEAD
# };
# PyObject * meth_foo() {
#     Py_RETURN_NONE;
# }
# ''', sys.stdout))

import cfly

core = cfly.build_module('core', '''
#include <Python.h>

struct Foo {
    PyObject_HEAD
};

PyObject * meth_foo() {
    Py_RETURN_NONE;
}
''')

print(core.foo())
