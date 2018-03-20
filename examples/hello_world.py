from cfly import module_from_source

mymodule = module_from_source('mymodule', '''
    #include <Python.h>

    PyObject * meth_hello(PyObject * self, PyObject * args) {
        return PyUnicode_FromFormat("Hello World!");
    }
''')

print(mymodule.hello())
