import importlib
import os
import re
import shutil
import subprocess
import sys
import hashlib
from distutils.ccompiler import new_compiler
from distutils.errors import DistutilsExecError, CompileError
from distutils.sysconfig import get_python_inc

from jinja2 import Template

from .data import source_template, module_template, tps

typename = r'[A-Za-z][A-Za-z0-9]*'
varname = r'[A-Za-z_][A-Za-z0-9_]*'
braces = r'(?:[^\{\}]*(?:\{(?:[^\{\}]*(?:\{(?:[^\{\}]*(?:\{[^\{\}]*\}[^\{\}]*)?)\}[^\{\}]*)?)\}[^\{\}]*)?)'

re_type = re.compile(f'^\\s*struct\\s+({typename})\\s*\\{{(\\n\\s*PyObject_HEAD\\n{braces})\\}};', re.M)
re_proc = re.compile(f'^\\s*({varname}(?:\\s*\\*)?)\\s*({typename})_({varname})\\s*\\(([^\\)]*)\\)\\s*\\{{', re.M)


class Meth:
    def __init__(self, rval, name, args):
        self.name = name
        self.flags = ['METH_NOARGS', 'METH_NOARGS', 'METH_VARARGS', 'METH_VARARGS | METH_KEYWORDS'][len(args.split(','))]
        self.args = args
        self.rval = rval


class GetSet:
    def __init__(self, name):
        self.name = name
        self.set = None
        self.get = None


class Type:
    def __init__(self, name, struct):
        self.name = name
        self.struct = struct
        self.methods = {}
        self.getset = {}


class Compiler:
    def __init__(self):
        self.compiler = new_compiler()
        self.compiler.initialize()

        if hasattr(sys, 'real_prefix'):
            self.compiler.add_library_dir(os.path.join(getattr(sys, 'real_prefix'), 'libs'))

        self.compiler.add_library_dir(os.path.join(sys.exec_prefix, 'libs'))
        self.compiler.add_library_dir(os.path.join(sys.base_exec_prefix, 'libs'))

    def compile(self, build_dir, sources, output, macros, include_dirs, library_dirs, libraries, exports, cache):

        def obj_file(source, build_dir):
            return os.path.splitext(os.path.join(build_dir, source))[0] + '.obj'

        include_dirs = (include_dirs or []) + [get_python_inc()]
        objects = [obj_file(source, build_dir) for source, original in sources]

        todo = []
        for pair, obj in zip(sources, objects):
            source, original = pair
            if os.path.isfile(obj) and os.path.getmtime(obj) > os.path.getmtime(original or source):
                continue
            todo.append(pair)

        if not cache:
            todo = sources

        if todo:
            for source, original in todo:
                extra = [os.path.abspath(os.path.dirname(original))] if original else []
                self.compiler.compile([source], build_dir, macros, extra + include_dirs)
            self.compiler.link('shared_object', objects, 'output', build_dir, libraries, library_dirs, [], exports)

            if os.path.isfile(output):
                try:
                    os.unlink(output)
                except PermissionError:
                    shutil.move(output, os.path.join(build_dir, f'_{os.urandom(8).hex()}'))
            shutil.move(os.path.join(build_dir, 'output'), output)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_source(source, build_log):
    module_methods = {}
    module_types = {name: Type(name, content) for name, content in re_type.findall(source)}

    for rval, typ, name, args in re_proc.findall(source):
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
                    setattr(module_types[typ].getset[rest], prefix, Meth(rval, f'{typ}_{name}', args))
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

    return module_methods, module_types


def is_up_to_date(filename, deps):
    if not os.path.isfile(filename):
        return False

    if not deps:
        return True

    return os.path.getmtime(filename) > max(os.path.getmtime(x) for x in deps)


def readall(folder, filename):
    filename = os.path.join(folder, filename)
    if not os.path.isfile(filename):
        return None
    with open(filename, 'r') as f:
        return f.read()


def writeall(folder, filename, content):
    filename = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(content)
    return filename


def args_checksum(*args):
    return hashlib.sha512(str(args).encode()).hexdigest()


def render_template(template, **kwargs):
    template = Template(
        template,
        block_start_string='/*%',
        block_end_string='%*/',
        variable_start_string='/*{',
        variable_end_string='}*/',
        line_statement_prefix='///',
    )
    code = template.render(**kwargs)
    code = re.sub(r'^//!$', '', code, flags=re.M)
    return code


def build_module(name, source=None, *, sources=None, preprocess=None, output=None, build_dir='build',
        include_dirs=None, library_dirs=None, libraries=None, macros=None, cache=True):

    if output is None:
        output = f'{name}.pyd'

    if sources is None:
        sources = []

    if preprocess is None:
        preprocess = []

    if source is None:
        source = ''

    preprocess_set = set(preprocess)
    sources = [x for x in sources if x not in preprocess_set]

    if source and sources + preprocess:
        raise ValueError('invalid arguments')

    os.makedirs(build_dir, exist_ok=True)

    module_home = os.path.join(build_dir, 'temp', name)
    old_checksum = readall(module_home, 'args.txt')
    checksum = args_checksum(
        name,
        source,
        sources,
        preprocess,
        output,
        build_dir,
        include_dirs,
        library_dirs,
        libraries,
        macros
    )

    if cache and checksum == old_checksum and is_up_to_date(output, sources):
        return load_module(name, output)

    with open(os.path.join(build_dir, 'build.log'), 'wb+') as build_log:
        shutil.rmtree(module_home, ignore_errors=True)
        os.makedirs(module_home, exist_ok=True)

        if source:
            preprocess = [writeall(module_home, 'source.cpp', source)]

        global_module_methods = {}
        global_module_types = {}

        sources = [(x, None) for x in sources]

        for filename in preprocess:
            source = readall('.', filename)
            module_methods, module_types = parse_source(source, build_log)
            global_module_methods.update(module_methods)
            global_module_types.update(module_types)
            code = render_template(source_template, module=name, types=module_types, methods=module_methods)
            sources.append((writeall(module_home, filename, source + code), filename))

        code = render_template(module_template, module=name, types=module_types, methods=module_methods)
        sources.append((writeall(module_home, 'module.cpp', code), None))
        exports = [f'PyInit_{name}']

        compiler = Compiler()

        def spawn(cmd):
            old_path = os.getenv('path')
            try:
                build_log.write('\nRunning:\n'.encode())
                for node in cmd:
                    build_log.write(f'\t{node}\n'.encode())
                build_log.write('\n'.encode())
                build_log.flush()
                os.environ['path'] = compiler.compiler._paths
                ret = subprocess.call(cmd, stdout=build_log, stderr=subprocess.STDOUT)
                if ret:
                    build_log.seek(0)
                    entire_log = build_log.read().decode()
                    raise DistutilsExecError(f'Compiler failed:\n{entire_log}')

            finally:
                build_log.flush()
                os.environ['path'] = old_path

        compiler.compiler.spawn = spawn

        try:
            compiler.compile(build_dir, sources, output, macros, include_dirs, library_dirs, libraries, exports, cache)
        except CompileError as ex:
            raise ex from None

        writeall(module_home, 'args.txt', checksum)

    return load_module(name, output)
