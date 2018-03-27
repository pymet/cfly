cfly
====

.. warning::

    CFly is under development. It may change without backward compatibility until the first stable version is reached. The first stable version will be 1.0.0

Installation
------------

Install cfly with :command:`pip`:

.. code-block:: sh

    $ pip install cfly

.. toctree::
    :maxdepth: 2

Reference
---------

.. py:module:: cfly
.. py:currentmodule:: cfly

.. autofunction:: build_module(name, source=None, sources=None, preprocess=None, output=None, build_dir='build', include_dirs=None, library_dirs=None, libraries=None, macros=None, cache=True) -> module

Examples
--------

Hello World
^^^^^^^^^^^

.. rubric:: hello_world.py

.. literalinclude:: ../examples/hello_world.py
    :linenos:

Arguments
^^^^^^^^^

.. rubric:: arguments.py

.. literalinclude:: ../examples/arguments.py
    :linenos:

Sample Project
^^^^^^^^^^^^^^

.. rubric:: sample_project.py

.. literalinclude:: ../examples/sample_project.py
    :linenos:

.. rubric:: something.hpp

.. literalinclude:: ../examples/sample_project/something.hpp
    :language: c++
    :linenos:

.. rubric:: something.cpp

.. literalinclude:: ../examples/sample_project/something.cpp
    :language: c++
    :linenos:

.. rubric:: module.cpp

.. literalinclude:: ../examples/sample_project/module.cpp
    :language: c++
    :linenos:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
