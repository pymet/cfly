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
opts['define_macros'] = [('CFLY', None)] + opts.get('define_macros', [])
ext = Extension('%(name)s', sources=['src.cpp'], **opts)
setup(name='%(name)s', version='1.0.0', ext_modules=[ext])
'''

CPP = '''
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#line 0 "__head__"
%(impl)s

#line 0 "__tail__"
PyMethodDef methods[] = {%(decl)s
{0},
};

PyModuleDef moduledef = {PyModuleDef_HEAD_INIT, "%(name)s", 0, -1, methods, 0, 0, 0, 0};

extern "C" PyObject * PyInit_%(name)s() {
	PyObject * module = PyModule_Create(&moduledef);
	return module;
}
'''

METHOD = '''
#line 0 "%(name)s"
PyObject * %(name)s(PyObject * self, PyObject * args) {
%(src)s
;return 0;
}
'''

METHOD_ENTRY = '\n{"%(name)s", (PyCFunction)%(name)s, METH_VARARGS, 0},'


def add_line_numbers(source) -> str:
    numbered = ''
    line_number = 0
    lines = source.split('\n')
    pad = next(x for x in range(10) if 10 ** x > len(lines))
    line_format = '/* %%%dd */ %%s\n' % pad
    for line in lines:
        if line.startswith('#line 0'):
            line_number = 0
            numbered += '\n%s\n' % line

        else:
            numbered += line_format % (line_number, line)
        line_number += 1
    return numbered


def raise_exception(*args, **kwargs):  # pylint: disable=unused-argument
    raise Exception('module was not compiled')


class CMethod:
    '''
        Wrapper over PyCFunction.
    '''

    __slots__ = ['f']

    def __init__(self, f=raise_exception):
        self.f = f

    def __call__(self, *args):
        return self.f(*args)


class CModule:
    '''
        Python module written in C/C++.
    '''

    def __init__(self, name=None, opts=None):
        if name is None:
            name = '_' + os.urandom(8).hex()

        if opts is None:
            opts = {}

        self.name = name
        self.opts = opts
        self.methods = []
        self.head = ''
        self.source = ''
        self.binary = None
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
                impl = self.head + '\n'
                decl = ''

                for meth in self.methods:
                    impl += METHOD % meth
                    decl += METHOD_ENTRY % meth

                self.source = CPP % {'name': self.name, 'impl': impl, 'decl': decl}
                f.write(self.source)

            cmd = [sys.executable, setup_py, 'build_ext', '--inplace']
            proc = Popen(cmd, cwd=tempdir, stdout=PIPE, stderr=STDOUT)
            proc.wait()

            os.unlink(setup_py)
            os.unlink(src_cpp)

            if proc.returncode:
                numbered = add_line_numbers(self.source)
                args = (numbered, proc.stdout.read().decode())
                raise Exception('Compiler failed:\nSource code:\n%s\nOutput:\n%s\n' % args)

            binary = next(x for x in os.listdir(tempdir) if x != 'build')
            binary1 = os.path.join(tempdir, binary)
            binary2 = os.path.join(tempfile.gettempdir(), binary)
            shutil.move(binary1, binary2)

            with open(binary2, 'rb') as f:
                self.binary = (binary, f.read())

            spec = importlib.util.spec_from_file_location(self.name, binary2)
            self.mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.mod)

            for meth in self.methods:
                meth['proc'].f = getattr(self.mod, meth['name'])

            self.methods = {meth['name']: meth['proc'] for meth in self.methods}

    def method(self, src, name=None) -> 'CMethod':
        '''
            PyCFunction with predefined args and return type.

            Template:
                PyObject * method(PyObject * self, PyObject * args);
        '''

        if name is None:
            name = 'unnamed_method_%d' % len(self.methods)

        proc = CMethod()
        self.methods.append({
            'name': name,
            'src': src,
            'proc': proc,
        })
        return proc

    def get(self, key):
        if self.mod is None:
            return None
        return self.methods.get(key)

    def save(self, path):
        fname, content = self.binary
        with open(os.path.join(path, fname), 'wb') as f:
            f.write(content)


def load_folder(path, extension='.cpp', headfile='__head__', name=None, opts=None) -> 'CModule':
    '''
        Load methods from a folder.
    '''

    cmod = CModule(name, opts)

    with cmod:
        for fname in os.listdir(path):
            if not fname.endswith(extension):
                continue

            with open(os.path.join(path, fname)) as f:
                if fname == headfile + extension:
                    cmod.head = f.read()
                else:
                    idx = fname[:-len(extension)]
                    cmod.method(f.read(), idx)

    return cmod
