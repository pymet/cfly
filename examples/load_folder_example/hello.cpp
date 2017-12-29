#ifndef CFLY
#include <Python.h>
#endif

PyObject * hello = PyUnicode_FromString("Hello World!");
PyObject_Print(hello, stdout, Py_PRINT_RAW);
Py_DECREF(hello);
Py_RETURN_NONE;
