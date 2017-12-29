from cfly import CModule

with CModule() as my_module:
    my_method = my_module.method('''
        int x = 3 // missing semicolon
        return PyUnicode_FromFormat("Hello World!");
    ''')

# syntax error: missing ';' before 'return'

print(my_method())
