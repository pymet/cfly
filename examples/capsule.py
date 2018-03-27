from cfly import build_module

mymodule = build_module('mymodule', source='''
    #include <Python.h>

    struct FooBar {
        int x, y, z;
    };

    PyObject * meth_mymethod1(PyObject * self, PyObject * args) {
        int x, y, z;

        if (!PyArg_ParseTuple(args, "iii", &x, &y, &z)) {
            return 0;
        }

        FooBar * res = new FooBar{x, y, z};
        return PyCapsule_New(res, "FooBar", 0);
    }

    PyObject * meth_mymethod2(PyObject * self, PyObject * args) {
        PyObject * capsule;

        if (!PyArg_ParseTuple(args, "O", &capsule)) {
            return 0;
        }

        FooBar * foobar = (FooBar *)PyCapsule_GetPointer(capsule, "FooBar");

        if (!foobar) {
            return 0;
        }

        return PyUnicode_FromFormat("FooBar {%d, %d, %d}", foobar->x, foobar->y, foobar->z);
    }
''')

foobar = mymodule.mymethod1(1, 2, 3)

print(foobar)
print(mymodule.mymethod2(foobar))
