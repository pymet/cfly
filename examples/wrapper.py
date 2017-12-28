from cfly import CModule

with CModule() as my_module:
    my_method = my_module.method('''
        const char * arg_str;
        int arg_int;

        if (!PyArg_ParseTuple(args, "si", &arg_str, &arg_int)) {
            return 0;
        }

        return PyUnicode_FromFormat("String: %s, Integer: %d", arg_str, arg_int);
    ''')


def wrap_my_method(cmethod):
    def method(message, number):
        return cmethod(message, number)
    return method


my_wrapped_method = wrap_my_method(my_method.f)

print(my_wrapped_method('Hello World!', 12345))
