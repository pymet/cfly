from cfly import module_from_source

mod = module_from_source('''
#define PY_SSIZE_T_CLEAN
#include <Python.h>

struct Foobar {
    PyObject_HEAD
};

PyObject * meth_hello_world(PyObject * self) {
    return PyLong_FromLong(1234);
}
''')

print(mod.Foobar)
print(mod.hello_world())
