import importlib.util
import os
import re
import shutil
import sys
import tempfile
from subprocess import PIPE, STDOUT, Popen


def iterall(*args):
    if len(args) == 1:
        args = args[0]
    for arg in args:
        yield from arg


typedef_template = '''
PyTypeObject %(name)s_Type = {
\tPyVarObject_HEAD_INIT(0, 0)
\t"%(module)s.%(name)s",
\tsizeof(%(name)s),
\t0,
\t(destructor)%(tp_dealloc)s,
\t0,
\t0,
\t0,
\t0,
\t(reprfunc)%(tp_repr)s,
\t%(tp_as_number)s,
\t%(tp_as_sequence)s,
\t%(tp_as_mapping)s,
\t0,
\t%(tp_call)s,
\t0,
\t0,
\t0,
\t%(tp_as_buffer)s,
\tPy_TPFLAGS_DEFAULT,
\t0,
\t0,
\t0,
\t0,
\t0,
\t0,
\t0,
\t%(tp_methods)s,
\t0,
\t%(tp_getset)s,
\t%(tp_base)s,
\t0,
\t0,
\t0,
\t0,
\t(initproc)%(tp_init)s,
\t0,
\t%(tp_new)s,
};
'''.strip('\n')

typeinit_template = '''
\tif (PyType_Ready(&%(name)s_Type) < 0) {
\t\tPyErr_Format(PyExc_ImportError, "Cannot register %(name)s in %%s (%%s:%%d)", __FUNCTION__, __FILE__, __LINE__);
\t\treturn 0;
\t}

\tPy_INCREF(&%(name)s_Type);
\tPyModule_AddObject(module, "%(name)s", (PyObject *)&%(name)s_Type);
'''.strip('\n')

moduledef_template = '''
PyModuleDef moduledef = {
\tPyModuleDef_HEAD_INIT,
\t"%(module)s",
\t0,
\t-1,
\tmodulemethods,
\t0,
\t0,
\t0,
\t0,
};
'''.strip('\n')

moduleinit_template = '''
extern "C" PyObject * PyInit_%(module)s() {
\tPyObject * module = PyModule_Create(&moduledef);

\tif (!module) {
\t\treturn module;
\t}

%(typeinits)s
\treturn module;
}
'''.strip('\n')

source_template = '''
%(source)s

#ifndef Py_PYTHON_H
#error "Missing #include <Python.h>"
#endif

%(typedefs)s

%(modulemethods)s

%(moduledef)s

%(moduleinit)s
'''.strip('\n')

setup_template = '''
from glob import glob
from setuptools import setup, Extension

opts = %(opts)r
opts['define_macros'] = [('CFLY', None)] + opts.get('define_macros', [])
ext = Extension('%(module)s', sources=glob('**/*.cpp', recursive=True), **opts)
setup(name='%(module)s', version='1.0.0', ext_modules=[ext])
'''

name = r'[A-Za-z_][A-Za-z0-9_]*'
args = r'(?:, (?:PyObject \* (args)(?:, (?:PyObject \* (kwds)))?))?'
closure = rf'(?:, void \* closure)?'

re_function = re.compile(rf'^\s*{name} \* meth_({name})\(PyObject \* self{args}\) \{{', flags=re.M)

re_tps = [
    re.compile(rf'^\s*{name} \* ({name})_(tp_new)(PyTypeObject \* type, PyObject \* args, PyObject \* kwds) \{{', flags=re.M),
    re.compile(rf'^\s*{name} \* ({name})_(tp_init)\(\1 \* self, PyObject \* args, PyObject \* kwds\) \{{', flags=re.M),
    re.compile(rf'^\s*{name} \* ({name})_(tp_dealloc)\(\1 \* self\) \{{', flags=re.M),
    re.compile(rf'^\s*{name} \* ({name})_(tp_repr)\(\1 \* self\) \{{', flags=re.M),
]

re_method = re.compile(rf'^\s*{name} \* ({name})_meth_({name})\(\1 \* self{args}\) \{{', flags=re.M)
re_getter = re.compile(rf'^\s*{name} \* ({name})_(get)_({name})\(\1 \* self{closure}\) \{{', flags=re.M)
re_setter = re.compile(rf'^\s*int ({name})_(set)_({name})\(\1 \* self, {name} \* {name}{closure}\) \{{', flags=re.M)
re_type = re.compile(rf'^\s*struct ({name}) \{{(?:(?:\s*//[^\n]*\n)*\s*)PyObject_HEAD', flags=re.M)


def compile_module(name, source, files=None, opts=None):
    '''
        Compile a module.

        Args:
            name (str): the name of the module.
            source (str): the source of the module.
            files (dict): extra source files.
            opts (dict): additional build options.

        Returns:
            path to the binary
    '''

    if files is None:
        files = {}

    if opts is None:
        opts = {}

    if isinstance(source, bytes):
        source = source.decode()

    module = name
    pytypes = re_type.findall(source)

    methods = {m: {} for m in pytypes}
    getset = {m: {} for m in pytypes}

    tp = {
        m: {
            'tp_init': 0,
            'tp_repr': 0,
            'tp_as_number': 0,
            'tp_as_sequence': 0,
            'tp_as_mapping': 0,
            'tp_as_buffer': 0,
            'tp_base': 0,
            'tp_call': 0,
            'tp_new': 0,
            'tp_dealloc': 0,
            'tp_methods': 0,
            'tp_getset': 0,
        }
        for m in pytypes
    }

    for m in re_method.finditer(source):
        name, method, args, kwds = m.groups()
        methods[name][method] = 'METH_VARARGS | METH_KEYWORDS' if kwds else 'METH_VARARGS' if args else 'METH_NOARGS'

    for m in sorted(iterall(re_getter.finditer(source), re_setter.finditer(source)), key=lambda m: m.span()):
        name, gs, propname = m.groups()
        getset[name].setdefault(propname, {'get': False, 'set': False})
        getset[name][propname][gs] = True

    for m in iterall(tp.finditer(source) for tp in re_tps):
        name, tp = m.groups()
        tp[name][tp] = f'{name}_{tp}'

    typedefs = []
    typeinits = []

    for name in pytypes:
        context = {
            'module': module,
            'name': name,
        }

        context.update(tp[name])

        if methods[name]:
            context['tp_methods'] = f'{name}_tp_methods'
            tp_methods_def = f'PyMethodDef {name}_tp_methods[] = {{\n'
            for meth, flags in methods[name].items():
                tp_methods_def += f'\t{{"{meth}", (PyCFunction){name}_meth_{meth}, {flags}, 0}},\n'
            tp_methods_def += f'\t{{0, 0, 0, 0}},\n'
            tp_methods_def += f'}};'
            typedefs.append(tp_methods_def)

        if methods[name]:
            context['tp_getset'] = f'{name}_tp_getset'
            tp_getset_def = f'PyGetSetDef {name}_tp_getset[] = {{\n'
            for prop, content in getset[name].items():
                getter = f'(getter){name}_get_{prop}' if content['get'] else '0'
                setter = f'(setter){name}_set_{prop}' if content['set'] else '0'
                tp_getset_def += f'\t{{(char *)"{prop}", {getter}, {setter}, 0, 0}},\n'
            tp_getset_def += f'\t{{0, 0, 0, 0, 0}},\n'
            tp_getset_def += f'}};'
            typedefs.append(tp_getset_def)

        typedefs.append(typedef_template % context)
        typeinits.append(typeinit_template % context)

    modulemethods = f'PyMethodDef modulemethods[] = {{\n'
    for m in re_function.finditer(source):
        meth, args, kwds = m.groups()
        flags = 'METH_VARARGS | METH_KEYWORDS' if kwds else 'METH_VARARGS' if args else 'METH_NOARGS'
        modulemethods += f'\t{{"{meth}", (PyCFunction)meth_{meth}, {flags}, 0}},\n'
    modulemethods += f'\t{{0, 0, 0, 0}},\n'
    modulemethods += f'}};'

    typedefs = '\n\n'.join(typedefs)
    moduledef = moduledef_template % {'module': module}
    moduleinit = moduleinit_template % {'module': module, 'typeinits': '\n\n'.join(x + '\n' for x in typeinits)}

    context = {
        'source': source,
        'typedefs': typedefs,
        'modulemethods': modulemethods,
        'moduledef': moduledef,
        'moduleinit': moduleinit,
        'module': module,
        'opts': opts,
    }

    all_files = {
        'module.cpp': (source_template % context).encode(),
        'setup.py': (setup_template % context).encode(),
    }

    all_files.update(files)

    with tempfile.TemporaryDirectory() as tempdir:
        for filename, source in all_files.items():
            filename = os.path.join(tempdir, filename)
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(source)

        cmd = [sys.executable, os.path.join(tempdir, 'setup.py'), 'build_ext', '--inplace']
        proc = Popen(cmd, cwd=tempdir, stdout=PIPE, stderr=STDOUT)
        output = proc.communicate()[0]

        if proc.returncode:
            raise Exception('Compiler failed:\n%s' % output.decode())

        proc.stdout.close()

        finaldir = tempfile.mkdtemp(prefix='cfly_')
        binary = next(x for x in os.listdir(tempdir) if x.endswith('.pyd') or x.endswith('.so'))
        binary1 = os.path.join(tempdir, binary)
        binary2 = os.path.join(finaldir, binary)
        shutil.move(binary1, binary2)
        return binary2


def module_from_source(name, source, files=None, opts=None):
    '''
        Compile and import a module.

        Args:
            name (str): the name of the module.
            source (str): the source of the module.
            files (dict): extra source files.
            opts (dict): additional build options.

        Returns:
            the imported module
    '''

    path = compile_module(name, source, files, opts)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
