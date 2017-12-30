import argparse
import os

from cfly import load_folder


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

hello = wrap_hello(_mod.get('hello').f)
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
    foobar_new = _mod.get('foobar_new').f
    foobar_hello = _mod.get('foobar_hello').f
    foobar_get_msg = _mod.get('foobar_get_msg').f
    foobar_set_msg = _mod.get('foobar_set_msg').f

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
    subparsers = parser.add_subparsers()
    parser.set_defaults(command=None)

    init = subparsers.add_parser('init')
    init.set_defaults(command='init')
    init.add_argument('module')
    init.add_argument('--template', default='hello')

    build = subparsers.add_parser('build')
    build.set_defaults(command='build')
    build.add_argument('module')
    build.add_argument('--name', default=None)

    args = parser.parse_args()
    if not args.command:
        parser.print_usage()
        exit()

    # args = parser.parse_args(['--help'])
    # args = parser.parse_args(['init', 'core', 'hello'])
    # args = parser.parse_args(['build', 'core'])
    # print(args)

    if args.command == 'build':
        cmod = load_folder(args.module, name=args.name)
        cmod.save(args.module)

    elif args.command == 'init':
        os.makedirs(args.module)

        if args.template == 'hello':
            with open(os.path.join(args.module, '__init__.py'), 'x') as f:
                f.write(HELLO_INIT)

            with open(os.path.join(args.module, '__head__.cpp'), 'x') as f:
                f.write(HELLO_HEAD)

            with open(os.path.join(args.module, 'hello.cpp'), 'x') as f:
                f.write(HELLO)

        elif args.template == 'foobar':
            with open(os.path.join(args.module, '__init__.py'), 'x') as f:
                f.write(FOOBAR_INIT)

            with open(os.path.join(args.module, '__head__.cpp'), 'x') as f:
                f.write(FOOBAR_HEAD)

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
