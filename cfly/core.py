import importlib
import os
import re
import shutil
import subprocess
import sys
from distutils.ccompiler import new_compiler
from distutils.errors import DistutilsExecError
from distutils.sysconfig import get_python_inc

from jinja2 import Template

from .data import template, tps

typename = r'[A-Za-z][A-Za-z0-9]*'
varname = r'[A-Za-z_][A-Za-z0-9_]*'
braces = r'(?:[^\{\}]*(?:\{(?:[^\{\}]*(?:\{(?:[^\{\}]*(?:\{[^\{\}]*\}[^\{\}]*)?)\}[^\{\}]*)?)\}[^\{\}]*)?)'

re_type = re.compile(f'^\\s*struct\\s+({typename})\\s*\\{{(\\n\\s*PyObject_HEAD\\n{braces})\\}};', re.M)
re_proc = re.compile(f'^\\s*({varname}(?:\\s*\\*)?)\\s*({typename})_({varname})\\s*\\(([^\\)]*)\\)\\s*\\{{', re.M)


def obj_file(source, build_dir):
    return os.path.splitext(os.path.join(build_dir, source))[0] + '.obj'


class Meth:
    def __init__(self, rval, name, args):
        self.name = name
        self.flags = ['METH_NOARGS', 'METH_NOARGS', 'METH_VARARGS', 'METH_VARARGS | METH_KEYWORDS'][len(args.split(','))]
        self.args = args
        self.rval = rval


class GetSet:
    def __init__(self, name):
        self.name = name


class Type:
    def __init__(self, name, struct):
        self.name = name
        self.struct = struct
        self.methods = {}
        self.getset = {}


class Compiler:
    def __init__(self, build_dir='build'):
        self.compiler = new_compiler()
        self.compiler.initialize()

        if hasattr(sys, 'real_prefix'):
            self.compiler.add_library_dir(os.path.join(getattr(sys, 'real_prefix'), 'libs'))

        self.compiler.add_library_dir(os.path.join(sys.exec_prefix, 'libs'))
        self.compiler.add_library_dir(os.path.join(sys.base_exec_prefix, 'libs'))
        self.build_dir = build_dir

    def compile(self, sources, output, macros, include_dirs, exports):
        objects = [obj_file(source, self.build_dir) for source in sources]

        todo = []
        for source, obj in zip(sources, objects):
            if os.path.isfile(obj) and os.path.getmtime(obj) > os.path.getmtime(source):
                continue
            todo.append(source)

        if todo:
            self.compiler.compile(todo, self.build_dir, macros, (include_dirs or []) + [get_python_inc()])
            self.compiler.link('shared_object', objects, 'output', self.build_dir, export_symbols=exports)

            if os.path.isfile(output):
                try:
                    os.unlink(output)
                except PermissionError:
                    shutil.move(output, os.path.join(self.build_dir, f'_{os.urandom(8).hex()}'))
            shutil.move(os.path.join(self.build_dir, 'output'), output)


def build_module(name, source=None, *, sources=None, preprocess=None, output=None, build_dir='build',
        include_dirs=None, library_dirs=None, libraries=None, macros=None, cache=True):

    module_name = name
    os.makedirs(build_dir, exist_ok=True)

    if output is None:
        output = f'{module_name}.pyd'

    if source is not None:
        cache = False

    module_home = os.path.join(build_dir, 'temp', module_name)

    if cache:
        args = [name, sources, preprocess, output, build_dir, include_dirs, library_dirs, libraries, macros]
        args = str(args).encode()
        args_file = os.path.join(module_home, 'args.txt')

        old_args = None
        if os.path.isfile(args_file):
            with open(args_file, 'rb') as f:
                old_args = f.read()

        if args == old_args and max(os.path.getmtime(x) for x in sources) < os.path.getmtime(output):
            spec = importlib.util.spec_from_file_location(module_name, output)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

    with open(os.path.join(build_dir, 'build.log'), 'wb+') as build_log:
        shutil.rmtree(module_home, ignore_errors=True)
        os.makedirs(module_home, exist_ok=True)

        if cache:
            with open(args_file, 'wb') as f:
                f.write(args)

        def create_source_file(name, content):
            name = os.path.join(module_home, name)
            os.makedirs(os.path.dirname(name), exist_ok=True)
            with open(name, 'wb') as f:
                f.write(content)
            return name

        if source is not None:
            if preprocess or sources:
                raise ValueError('invalid arguments')

            if isinstance(source, str):
                source = source.encode()
            preprocess = [create_source_file('source.cpp', source)]
            sources = preprocess

        type_matches = []
        proc_matches = []

        for fn in preprocess or []:
            with open(fn, 'r') as f:
                code = f.read()
                type_matches.extend(re_type.finditer(code))
                proc_matches.extend(re_proc.finditer(code))

        module_types = {m.group(1): Type(m.group(1), m.group(2)) for m in type_matches}

        module_methods = {}

        for match in proc_matches:
            rval, typ, name, args = match.groups()
            if typ == 'meth':
                module_methods[name] = Meth(rval, name, args)

            elif typ in module_types:
                name_match = re.match(r'([^_]+)_(.*)', name)

                if name_match:
                    prefix, rest = name_match.groups()

                    if prefix == 'meth':
                        module_types[typ].methods.setdefault(rest, Meth(rval, rest, args))
                        setattr(module_types[typ], 'tp_methods', f'{typ}_tp_methods')

                    elif prefix in ('get', 'set'):
                        module_types[typ].getset.setdefault(rest, GetSet(rest))
                        setattr(module_types[typ].getset[rest], prefix, Meth(rval, f'{typ}_{rest}', args))
                        setattr(module_types[typ], 'tp_getset', f'{typ}_tp_getset')

                    elif prefix in ('am', 'mp', 'nb', 'sq', 'tp'):
                        if re.match('(' + '|'.join(tps) + ')', name):
                            setattr(module_types[typ], name, f'{typ}_{name}')

                        else:
                            build_log.write(f'Unknown {name} for {typ}_{name}\n'.encode())

                    else:
                        build_log.write(f'Unknown prefix "{prefix}" in {typ}_{name}\n'.encode())

                else:
                    build_log.write(f'If {typ}_{name} is a method rename it to {typ}_meth_{name}\n'.encode())

            else:
                build_log.write(f'Unknown type {typ} in {typ}_{name}\n'.encode())

        build_log.flush()

        tmplt = Template(
            template,
            block_start_string='/*%',
            block_end_string='%*/',
            variable_start_string='/*{',
            variable_end_string='}*/',
            line_statement_prefix='///',
        )

        code = tmplt.render(module=module_name, types=module_types, methods=module_methods)
        code = re.sub(r'^//!$', '', code, flags=re.M).encode()
        sources = (sources or []) + [create_source_file('module.cpp', code)]

        compiler = Compiler(build_dir)

        def spawn(cmd):
            old_path = os.getenv('path')
            try:
                os.environ['path'] = compiler.compiler._paths
                ret = subprocess.call(cmd, stdout=build_log, stderr=subprocess.STDOUT)
                if ret:
                    build_log.seek(0)
                    entire_log = build_log.read().decode()
                    raise DistutilsExecError(f'Compiler failed:\n{entire_log}') from None

            finally:
                os.environ['path'] = old_path

        compiler.compiler.spawn = spawn
        for libdir in library_dirs or []:
            compiler.compiler.add_library_dir(libdir)
        compiler.compile(sources, output, include_dirs, macros, [f'PyInit_{module_name}'])

    spec = importlib.util.spec_from_file_location(module_name, output)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
