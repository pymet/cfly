from cfly import CModule

with CModule() as my_module:
    my_method = my_module.method('''
        return PyUnicode_FromFormat("Hello World!");
    ''')

print(my_method())
