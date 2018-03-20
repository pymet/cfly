from cfly import module_from_source

mymodule = module_from_source('mymodule', '''
    #include <Python.h>

    PyObject * meth_hello(PyObject * self, PyObject * args) {
        int x = 3 // missing semicolon
        return PyUnicode_FromFormat("Hello World!");
    }
''')

# syntax error: missing ';' before 'return'

print(mymodule.hello())
