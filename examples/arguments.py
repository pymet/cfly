from cfly import build_module

mymodule = build_module('mymodule', '''
    #include <Python.h>

    PyObject * meth_mymethod(PyObject * self, PyObject * args) {
        const char * arg_str;
        int arg_int;

        if (!PyArg_ParseTuple(args, "si", &arg_str, &arg_int)) {
            return 0;
        }

        return PyUnicode_FromFormat("String: %s, Integer: %d", arg_str, arg_int);
    }
''')

print(mymodule.mymethod('Hello World!', 12345))
