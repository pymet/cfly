from cfly import CModule

opts = {
    'extra_compile_args': ['-std=c++11'],
}

with CModule(opts=opts) as my_module:
    my_module.head = '''
        struct FooBar {
            int x, y, z;
        };
    '''

    my_method1 = my_module.method('''
        int x, y, z;

        if (!PyArg_ParseTuple(args, "iii", &x, &y, &z)) {
            return 0;
        }

        FooBar * res = new FooBar{x, y, z};
        return PyCapsule_New(res, "FooBar", 0);
    ''')

    my_method2 = my_module.method('''
        PyObject * capsule;

        if (!PyArg_ParseTuple(args, "O", &capsule)) {
            return 0;
        }

        FooBar * foobar = (FooBar *)PyCapsule_GetPointer(capsule, "FooBar");

        if (!foobar) {
            return 0;
        }

        return PyUnicode_FromFormat("FooBar {%d, %d, %d}", foobar->x, foobar->y, foobar->z);
    ''')

foobar = my_method1(1, 2, 3)

print(foobar)
print(my_method2(foobar))
