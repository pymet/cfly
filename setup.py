from setuptools import setup


# python -m m2r README.md

long_description = '''
cfly
====

* Build python extensions on-the-fly.
* Run C++ code directly from Python.

Links
-----

* `Documentation <https://cfly.readthedocs.io>`_
* `cfly on Github <https://github.com/pymet/cfly>`_
* `cfly on PyPI <https://pypi.org/project/cfly>`_

Example
-------

.. code-block:: py

   from cfly import build_module

   mymodule = build_module('mymodule', \'\'\'
   #define PY_SSIZE_T_CLEAN
   #include <Python.h>

   struct Foobar {
       PyObject_HEAD
   };

   PyObject * meth_hello_world(PyObject * self) {
       return PyLong_FromLong(1234);
   }
   \'\'\')

   print(mymodule.Foobar)
   print(mymodule.hello_world())

**output**

.. code-block:: py

   <class 'mymodule.Foobar'>
   1234
'''


setup(
    name='cfly',
    version='0.9.13',
    description='Build python extensions on-the-fly. Run C++ code directly from Python',
    long_description=long_description,
    url='https://github.com/pymet/cfly',
    packages=['cfly'],
    install_requires=['jinja2'],
    author='pymet',
    author_email='office@pymet.com',
    license='MIT',
    classifiers=[],
    keywords=['cfly', 'build', 'extension', 'c++'],
)
