from cfly import CModule

with CModule() as my_module:
    my_module.head = '''
        #include <cmath>
    '''
    my_method = my_module.method('''
        return PyFloat_FromDouble(sqrt(2.0));
    ''')

print(my_method())
