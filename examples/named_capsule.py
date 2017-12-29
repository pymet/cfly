from cfly import CModule

with CModule() as my_module:
    my_method1 = my_module.method('''
        return PyCapsule_New("Hello World!", "Foo", 0);
    ''')

    my_method2 = my_module.method('''
        return PyCapsule_New("Hello World!", "Bar", 0);
    ''')

    my_method3 = my_module.method('''
        PyObject * capsule;

        if (!PyArg_ParseTuple(args, "O", &capsule)) {
            return 0;
        }

        const char * message = (const char *)PyCapsule_GetPointer(capsule, "Foo");

        if (!message) {
            return 0;
        }

        return PyUnicode_FromFormat("The message is: %s", message);
    ''')

obj1 = my_method1()
obj2 = my_method2()

print(obj1)
print(obj2)
print(my_method3(obj1))
print(my_method3(obj2))  # ValueError: PyCapsule_GetPointer called with incorrect name
