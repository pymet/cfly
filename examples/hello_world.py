from cfly import build_module

mymodule = build_module('mymodule', '''
    #include <Python.h>

    PyObject * meth_hello(PyObject * self, PyObject * args) {
        return PyUnicode_FromFormat("Hello World!");
    }
''')

print(mymodule.hello())
