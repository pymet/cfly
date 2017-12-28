# cfly

Build python extensions on-the-fly.

## Wrapping methods

```py
with CModule() as my_module:
    my_method = my_module.method(...)

# wrapper function for my_method
def wrap(f):
    def method(*args):
        return f(*args)
    return method

# wrap my_method
my_method = wrap(my_method.f)
```

## Under the hood

This section will explain what happens under the hood in the Hello World example.

```py
from cfly import CModule

with CModule() as my_module:
    my_method = my_module.method('''
        return PyUnicode_FromFormat("Hello World!");
    ''')

print(my_method())
```

The calls above are almost equivalent with the compiled version of the following python module written in C/C++.

```cpp
#define PY_SSIZE_T_CLEAN
#include <Python.h>

PyObject * method_0(PyObject * self, PyObject * args) {
	return PyUnicode_FromFormat("Hello World!");
}

PyMethodDef methods[] = {
	{"method_0", (PyCFunction)method_0, METH_VARARGS, 0},
	{0},
};

PyModuleDef moduledef = {PyModuleDef_HEAD_INIT, "module", 0, -1, methods, 0, 0, 0, 0};

extern "C" PyObject * PyInit_module() {
	PyObject * module = PyModule_Create(&moduledef);
	return module;
}
```

The `method_0` is wrapped with a CMethod class.

```py
class CMethod:
    __slots__ = ['f']
    ...

# my_method = my_module.method(...) will return a CMethod
# when leaving the with statement my_method.f will be equal to method_0
# calling my_method() will call my_method.f()
```
