import argparse
import os


def fmt(src):
    return src.strip() + '\n'


HELLO_INIT = fmt('''
import os

from cfly import load_folder

_mod = load_folder(os.path.dirname(__file__))

def wrap_hello(f):
    def method():
        return f()
    return method

hello = wrap_hello(_mod['hello'].f)
''')

HELLO_HEAD = fmt('''
#ifndef CFLY
#include <Python.h>
#endif
''')

HELLO = fmt('''
#ifndef CFLY
#include <Python.h>
#endif

if (!PyArg_ParseTuple(args, "")) {
    return 0;
}

PyObject * hello = PyUnicode_FromString("Hello World!\\n");
PyObject_Print(hello, stdout, Py_PRINT_RAW);
Py_DECREF(hello);
Py_RETURN_NONE;
''')

FOOBAR_INIT = fmt('''
import os

from cfly import load_folder

_mod = load_folder(os.path.dirname(__file__))

def wrap_foobar():
    foobar_new = _mod['foobar_new'].f
    foobar_hello = _mod['foobar_hello'].f
    foobar_get_msg = _mod['foobar_get_msg'].f
    foobar_set_msg = _mod['foobar_set_msg'].f

    class Foobar():
        __slots__ = ['_obj']

        def __init__(self):
            self._obj = foobar_new()

        def hello(self):
            return foobar_hello(self._obj)

        @property
        def msg(self):
            return foobar_get_msg(self._obj)

        @msg.setter
        def msg(self, value):
            foobar_set_msg(self._obj, value)

    return Foobar

Foobar = wrap_foobar()
''')

FOOBAR_HEAD = fmt('''
#ifndef CFLY
#include <Python.h>
#endif

struct Foobar {
    PyObject * msg;
};
''')

FOOBAR_NEW = fmt('''
#ifndef CFLY
#include <Python.h>
#endif

Foobar * foobar = new Foobar();

Py_INCREF(Py_None);
foobar->msg = Py_None;

return PyCapsule_New(foobar, "Foobar", 0);
''')

FOOBAR_HELLO = fmt('''
#ifndef CFLY
#include <Python.h>
#endif

PyObject * capsule;

if (!PyArg_ParseTuple(args, "O", &capsule)) {
    return 0;
}

Foobar * foobar = (Foobar *)PyCapsule_GetPointer(capsule, "Foobar");

if (!foobar) {
    return 0;
}

PyObject_Print(foobar->msg, stdout, Py_PRINT_RAW);
Py_RETURN_NONE;
''')

FOOBAR_GET_MSG = fmt('''
#ifndef CFLY
#include <Python.h>
#endif

PyObject * capsule;

if (!PyArg_ParseTuple(args, "O", &capsule)) {
    return 0;
}

Foobar * foobar = (Foobar *)PyCapsule_GetPointer(capsule, "Foobar");

if (!foobar) {
    return 0;
}

Py_INCREF(foobar->msg);
return foobar->msg;
''')

FOOBAR_SET_MSG = fmt('''
#ifndef CFLY
#include <Python.h>
#endif

PyObject * capsule;
PyObject * msg;

if (!PyArg_ParseTuple(args, "OO", &capsule, &msg)) {
    return 0;
}

Foobar * foobar = (Foobar *)PyCapsule_GetPointer(capsule, "Foobar");

if (!foobar) {
    return 0;
}

Py_INCREF(msg);
Py_DECREF(foobar->msg);
foobar->msg = msg;
Py_RETURN_NONE;
''')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('cfly')
    parser.add_argument('module')
    parser.add_argument('template', nargs='?', default='hello')
    args = parser.parse_args()

    os.makedirs(args.module)

    if args.template == 'hello':
        with open(os.path.join(args.module, '__init__.py'), 'x') as f:
            f.write(HELLO_INIT)

        with open(os.path.join(args.module, '__head__.cpp'), 'x') as f:
            f.write(HELLO_HEAD)

        with open(os.path.join(args.module, 'hello.cpp'), 'x') as f:
            f.write(HELLO)

    elif args.template == 'foobar':
        with open(os.path.join(args.module, 'foobar_new.cpp'), 'x') as f:
            f.write(FOOBAR_NEW)

        with open(os.path.join(args.module, 'foobar_hello.cpp'), 'x') as f:
            f.write(FOOBAR_HELLO)

        with open(os.path.join(args.module, 'foobar_get_msg.cpp'), 'x') as f:
            f.write(FOOBAR_GET_MSG)

        with open(os.path.join(args.module, 'foobar_set_msg.cpp'), 'x') as f:
            f.write(FOOBAR_SET_MSG)

    else:
        raise Exception()
