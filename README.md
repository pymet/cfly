# cfly

- Build python extensions on-the-fly.
- Run C++ code directly from Python.

## Example

```py
from cfly import build_module

mymodule = build_module('mymodule', '''
#define PY_SSIZE_T_CLEAN
#include <Python.h>

struct Foobar {
    PyObject_HEAD
};

PyObject * meth_hello_world(PyObject * self) {
    return PyLong_FromLong(1234);
}
''')

print(mymodule.Foobar)
print(mymodule.hello_world())
```

**output**

```py
<class 'mymodule.Foobar'>
1234
```
