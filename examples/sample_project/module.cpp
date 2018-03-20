#include "something.hpp"

#include <Python.h>

PyObject * meth_get_x(PyObject * self) {
    return PyLong_FromLong(x);
}
