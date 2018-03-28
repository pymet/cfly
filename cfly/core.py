import hashlib
import importlib
import os
import re
import shutil
import subprocess
import sys
from distutils.ccompiler import new_compiler
from distutils.errors import CompileError, DistutilsExecError
from distutils.sysconfig import get_python_inc

from jinja2 import Template

from .data import module_template, proc_pattern, source_template, tps, type_pattern

re_type = re.compile(type_pattern, re.M)
re_proc = re.compile(proc_pattern, re.M)

flags = ['METH_NOARGS', 'METH_NOARGS', 'METH_VARARGS', 'METH_VARARGS | METH_KEYWORDS']


class Meth:
    def __init__(self, rval, name, args):
        self.name = name
        self.flags = flags[len(args.split(','))]
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


def create_compiler():
    compiler = new_compiler()
    compiler.initialize()

    if hasattr(sys, 'real_prefix'):
        compiler.add_library_dir(os.path.join(getattr(sys, 'real_prefix'), 'libs'))

    compiler.add_library_dir(os.path.join(sys.exec_prefix, 'libs'))
    compiler.add_library_dir(os.path.join(sys.base_exec_prefix, 'libs'))
    compiler.add_include_dir(get_python_inc())
    return compiler


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
                    setattr(module_types[typ], 'tp_methods', '%(typ)s_tp_methods' % locals())

                elif prefix in ('get', 'set'):
                    module_types[typ].getset.setdefault(rest, GetSet(rest))
                    setattr(module_types[typ].getset[rest], prefix, Meth(rval, '%(typ)s_%(name)s' % locals(), args))
                    setattr(module_types[typ], 'tp_getset', '%(typ)s_tp_getset' % locals())

                elif prefix in ('am', 'mp', 'nb', 'sq', 'tp'):
                    if re.match('(' + '|'.join(tps) + ')', name):
                        setattr(module_types[typ], name, '%(typ)s_%(name)s' % locals())

                    else:
                        build_log.write(('Unknown %(name)s for %(typ)s_%(name)s\n' % locals()).encode())

                else:
                    build_log.write(('Unknown prefix "%(prefix)s" in %(typ)s_%(name)s\n' % locals()).encode())

            else:
                build_log.write(('%(typ)s_%(name)s should be %(typ)s_meth_%(name)s\n' % locals()).encode())

        else:
            build_log.write(('Unknown type %(typ)s in %(typ)s_%(name)s\n' % locals()).encode())

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


def obj_file(source, build_dir):
    return os.path.splitext(os.path.join(build_dir, source))[0] + '.obj'


def build_module(
        name, source=None, *, sources=None, preprocess=None, output=None, build_dir='build',
        include_dirs=None, library_dirs=None, libraries=None, macros=None, cache=True):

    '''
        Args:
            name (str): The module name (must be unique).
            source (str): the source code in C++.

        Keyword Args:
            sources (str): Source files.
            preprocess (str): Source files that need cfly's preprocessing.
            output (str): The output file. defaults to '{name}.pyd'.
            build_dir (str): The build directory. defaults to 'build'.
            include_dirs (list): Additional include directories.
            library_dirs (list): Additional library directories.
            libraries (list): Additional libraries.
            macros (list): Predefined macros. (name, value) pairs.
            cache (bool): Enable cache.

        Returns:
            the compiled and imported module.
    '''

    if output is None:
        output = name + '.pyd'

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

    if checksum != old_checksum:
        cache = False

    if cache and is_up_to_date(output, sources):
        return load_module(name, output)

    with open(os.path.join(build_dir, name + '.log'), 'wb+') as build_log:
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

        code = render_template(module_template, module=name, types=global_module_types, methods=global_module_methods)
        sources.append((writeall(module_home, 'module.cpp', code), None))
        exports = ['PyInit_' + name]

        compiler = create_compiler()

        def spawn(cmd):
            old_path = os.getenv('path')
            try:
                os.environ['path'] = compiler._paths
                ret = subprocess.call(cmd, stdout=build_log, stderr=subprocess.STDOUT)
                if ret:
                    build_log.seek(0)
                    entire_log = build_log.read().decode()
                    raise DistutilsExecError('Compiler failed:\n' + entire_log)

            finally:
                build_log.flush()
                os.environ['path'] = old_path

        compiler.spawn = spawn

        for include_dir in include_dirs or []:
            compiler.add_include_dir(include_dir)

        for library_dir in library_dirs or []:
            compiler.add_library_dir(library_dir)

        try:
            objects = [obj_file(source, build_dir) for source, original in sources]

            todo = []
            for pair, obj in zip(sources, objects):
                source, original = pair
                if not is_up_to_date(obj, [original or source]):
                    todo.append(pair)

            if not cache:
                todo = sources

            if todo:
                for source, original in todo:
                    original_folder = [os.path.abspath(os.path.dirname(original))] if original else []
                    compiler.compile([source], build_dir, macros, original_folder)
                compiler.link('shared_object', objects, 'output', build_dir, libraries, [], [], exports)

                if os.path.isfile(output):
                    try:
                        os.unlink(output)
                    except PermissionError:
                        shutil.move(output, os.path.join(build_dir, '_' + os.urandom(8).hex()))
                shutil.move(os.path.join(build_dir, 'output'), output)

        except CompileError as ex:
            raise ex from None

        writeall(module_home, 'args.txt', checksum)

    return load_module(name, output)
