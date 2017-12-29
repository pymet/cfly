from cfly import CModule

with CModule() as my_module:
    my_method1 = my_module.method('''
        return PyCapsule_New("Hello World!", 0, 0);
    ''')

    my_method2 = my_module.method('''
        PyObject * capsule;

        if (!PyArg_ParseTuple(args, "O", &capsule)) {
            return 0;
        }

        return PyUnicode_FromFormat("The message is: %s", PyCapsule_GetPointer(capsule, 0));
    ''')

print(my_method2(my_method1()))
