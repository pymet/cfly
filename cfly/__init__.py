'''
    Build python extensions on-the-fly.
'''

import importlib.util
import os
import shutil
import sys
import tempfile
from subprocess import PIPE, STDOUT, Popen

__all__ = ['CModule', 'CMethod']

SETUP = '''
from setuptools import setup, Extension

opts = %(opts)r
ext = Extension('%(name)s', sources=['src.cpp'], **opts)
setup(name='%(name)s', version='1.0.0', ext_modules=[ext])
'''

CPP = '''
#define PY_SSIZE_T_CLEAN
#include <Python.h>

%(impl)s

PyMethodDef methods[] = {
    %(decl)s
	{0},
};

PyModuleDef moduledef = {PyModuleDef_HEAD_INIT, "%(name)s", 0, -1, methods, 0, 0, 0, 0};

extern "C" PyObject * PyInit_%(name)s() {
	PyObject * module = PyModule_Create(&moduledef);
	return module;
}
'''

METHOD = 'PyObject * %(name)s(PyObject * self, PyObject * args) {\n%(src)s;\nreturn 0;}\n'
METHOD_ENTRY = '{"%(name)s", (PyCFunction)%(name)s, %(args)s, 0},\n'


def raise_exception(*args, **kwargs):  # pylint: disable=unused-argument
    raise Exception('module was not compiled')


class CMethod:
    '''
        Wrapper over PyCFunction.
    '''

    __slots__ = ['f']

    def __init__(self):
        self.f = raise_exception

    def __call__(self, *args):
        return self.f(*args)


class CModule:
    '''
        Python module written in C/C++.
    '''

    def __init__(self, name=None, opts=None):
        if name is None:
            name = os.urandom(8).hex()

        if opts is None:
            opts = {}

        self.name = name
        self.opts = opts
        self.methods = []
        self.extra = ''
        self.mod = None

    def __enter__(self) -> 'CModule':
        return self

    def __exit__(self, *args):
        with tempfile.TemporaryDirectory() as tempdir:
            setup_py = os.path.join(tempdir, 'setup.py')
            src_cpp = os.path.join(tempdir, 'src.cpp')

            with open(setup_py, 'w') as f:
                f.write(SETUP % {'name': self.name, 'opts': self.opts})

            with open(src_cpp, 'w') as f:
                impl = self.extra + '\n'
                decl = ''

                for meth in self.methods:
                    impl += METHOD % meth
                    decl += METHOD_ENTRY % meth

                f.write(CPP % {'name': self.name, 'impl': impl, 'decl': decl})

            cmd = [sys.executable, setup_py, 'build_ext', '--inplace']
            proc = Popen(cmd, cwd=tempdir, stdout=PIPE, stderr=STDOUT)
            proc.wait()

            os.unlink(setup_py)
            os.unlink(src_cpp)

            if proc.returncode:
                raise Exception('compiler failed\n' + proc.stdout.read().decode())

            binary = next(x for x in os.listdir(tempdir) if x != 'build')
            binary1 = os.path.join(tempdir, binary)
            binary2 = os.path.join(tempfile.gettempdir(), binary)
            shutil.move(binary1, binary2)

            spec = importlib.util.spec_from_file_location(self.name, binary2)
            self.mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.mod)

            for meth in self.methods:
                meth['proc'].f = getattr(self.mod, meth['name'])

    def method(self, src, args=True) -> 'CMethod':
        '''
            PyCFunction with predefined args and return type.

            Template:
                PyObject * method(PyObject * self, PyObject * args);
        '''

        proc = CMethod()
        self.methods.append({
            'args': 'METH_VARARGS' if args else 'METH_NOARGS',
            'name': 'method_%d' % len(self.methods),
            'src': src,
            'proc': proc,
        })
        return proc
