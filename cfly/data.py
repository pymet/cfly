tps = [
    'am_aiter',
    'am_anext',
    'am_await',
    'bf_getbuffer',
    'bf_releasebuffer',
    'mp_ass_subscript',
    'mp_length',
    'mp_subscript',
    'nb_absolute',
    'nb_add',
    'nb_and',
    'nb_bool',
    'nb_divmod',
    'nb_float',
    'nb_floor_divide',
    'nb_index',
    'nb_inplace_add',
    'nb_inplace_and',
    'nb_inplace_floor_divide',
    'nb_inplace_lshift',
    'nb_inplace_matrix_multiply',
    'nb_inplace_multiply',
    'nb_inplace_or',
    'nb_inplace_power',
    'nb_inplace_remainder',
    'nb_inplace_rshift',
    'nb_inplace_subtract',
    'nb_inplace_true_divide',
    'nb_inplace_xor',
    'nb_int',
    'nb_invert',
    'nb_lshift',
    'nb_matrix_multiply',
    'nb_multiply',
    'nb_negative',
    'nb_or',
    'nb_positive',
    'nb_power',
    'nb_remainder',
    'nb_rshift',
    'nb_subtract',
    'nb_true_divide',
    'nb_xor',
    'sq_ass_item',
    'sq_concat',
    'sq_contains',
    'sq_inplace_concat',
    'sq_inplace_repeat',
    'sq_item',
    'sq_length',
    'sq_repeat',
    'tp_alloc',
    'tp_as_async',
    'tp_as_buffer',
    'tp_as_mapping',
    'tp_as_number',
    'tp_as_sequence',
    'tp_base',
    'tp_call',
    'tp_clear',
    'tp_dealloc',
    'tp_del',
    'tp_free',
    'tp_getattro',
    'tp_getset',
    'tp_hash',
    'tp_init',
    'tp_iter',
    'tp_iternext',
    'tp_methods',
    'tp_new',
    'tp_repr',
    'tp_reprfunc',
    'tp_richcompare',
    'tp_setattro',
    'tp_traverse',
]

prefixes = {
    'am': 'tp_as_async',
    'bf': 'tp_as_buffer',
    'mp': 'tp_as_mapping',
    'nb': 'tp_as_number',
    'sq': 'tp_as_sequence',
    'tp': None,
}

type_pattern = r'^\s*struct\s+([A-Za-z][A-Za-z0-9]*)\s*\{(\n\s*PyObject_HEAD\n(?:[^\{\}]*(?:\{(?:[^\{\}]*(?:\{(?:[^\{\}]*(?:\{[^\{\}]*\}[^\{\}]*)?)\}[^\{\}]*)?)\}[^\{\}]*)?))\};'
proc_pattern = r'^\s*([A-Za-z_][A-Za-z0-9_]*(?:\s*\*)?)\s*([A-Za-z][A-Za-z0-9]*)_([A-Za-z_][A-Za-z0-9_]*)\s*\(([^\)]*)\)\s*\{'

source_template = '''\
//!
#include <Python.h>
//!
/// if methods
/// for meth in methods.values()
PyCFunction __meth_/*{meth.name}*/ = (PyCFunction)meth_/*{meth.name}*/;
/// endfor
//!
/// endif
/// for typ in types.values()
/// if typ.tp_methods
PyMethodDef /*{typ.name}*/_tp_methods[] = {
/// for meth in typ.methods.values()
    {"/*{meth.name}*/", (PyCFunction)/*{typ.name}*/_meth_/*{meth.name}*/, /*{meth.flags}*/, "/*{module}*/./*{typ.name}*/./*{meth.name}*/"},
/// endfor
    {0, 0, 0, 0},
};
//!
/// endif
/// if typ.tp_getset
PyGetSetDef /*{typ.name}*/_tp_getset[] = {
/// for getset in typ.getset.values()
    {"/*{getset.name}*/", (getter)/*{ getset.get.name or 0 }*/, (setter)/*{ getset.set.name or 0 }*/, "/*{module}*/./*{typ.name}*/./*{getset.name}*/", 0},
/// endfor
    {0, 0, 0, 0, 0},
};
//!
/// endif
/// if typ.tp_as_number
PyNumberMethods /*{typ.name}*/_tp_as_number = {
    (binaryfunc)/*{ typ.nb_add or 0 }*/,
    (binaryfunc)/*{ typ.nb_subtract or 0 }*/,
    (binaryfunc)/*{ typ.nb_multiply or 0 }*/,
    (binaryfunc)/*{ typ.nb_remainder or 0 }*/,
    (binaryfunc)/*{ typ.nb_divmod or 0 }*/,
    (ternaryfunc)/*{ typ.nb_power or 0 }*/,
    (unaryfunc)/*{ typ.nb_negative or 0 }*/,
    (unaryfunc)/*{ typ.nb_positive or 0 }*/,
    (unaryfunc)/*{ typ.nb_absolute or 0 }*/,
    (inquiry)/*{ typ.nb_bool or 0 }*/,
    (unaryfunc)/*{ typ.nb_invert or 0 }*/,
    (binaryfunc)/*{ typ.nb_lshift or 0 }*/,
    (binaryfunc)/*{ typ.nb_rshift or 0 }*/,
    (binaryfunc)/*{ typ.nb_and or 0 }*/,
    (binaryfunc)/*{ typ.nb_xor or 0 }*/,
    (binaryfunc)/*{ typ.nb_or or 0 }*/,
    (unaryfunc)/*{ typ.nb_int or 0 }*/,
    0,
    (unaryfunc)/*{ typ.nb_float or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_add or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_subtract or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_multiply or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_remainder or 0 }*/,
    (ternaryfunc)/*{ typ.nb_inplace_power or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_lshift or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_rshift or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_and or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_xor or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_or or 0 }*/,
    (binaryfunc)/*{ typ.nb_floor_divide or 0 }*/,
    (binaryfunc)/*{ typ.nb_true_divide or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_floor_divide or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_true_divide or 0 }*/,
    (unaryfunc)/*{ typ.nb_index or 0 }*/,
    (binaryfunc)/*{ typ.nb_matrix_multiply or 0 }*/,
    (binaryfunc)/*{ typ.nb_inplace_matrix_multiply or 0 }*/,
};
//!
/// endif
/// if typ.tp_as_sequence
PySequenceMethods /*{typ.name}*/_tp_as_sequence = {
    (lenfunc)/*{ typ.sq_length or 0 }*/,
    (binaryfunc)/*{ typ.sq_concat or 0 }*/,
    (ssizeargfunc)/*{ typ.sq_repeat or 0 }*/,
    (ssizeargfunc)/*{ typ.sq_item or 0 }*/,
    0,
    (ssizeobjargproc)/*{ typ.sq_ass_item or 0 }*/,
    0,
    (objobjproc)/*{ typ.sq_contains or 0 }*/,
    (binaryfunc)/*{ typ.sq_inplace_concat or 0 }*/,
    (ssizeargfunc)/*{ typ.sq_inplace_repeat or 0 }*/,
};
//!
/// endif
/// if typ.tp_as_mapping
PyMappingMethods /*{typ.name}*/_tp_as_mapping = {
    (lenfunc)/*{ typ.mp_length or 0 }*/,
    (binaryfunc)/*{ typ.mp_subscript or 0 }*/,
    (objobjargproc)/*{ typ.mp_ass_subscript or 0 }*/,
};
//!
/// endif
/// if typ.tp_as_async
PyAsyncMethods /*{typ.name}*/_tp_as_async = {
    (unaryfunc)/*{ typ.am_await or 0 }*/,
    (unaryfunc)/*{ typ.am_aiter or 0 }*/,
    (unaryfunc)/*{ typ.am_anext or 0 }*/,
};
//!
/// endif
/// if typ.tp_as_buffer
PyBufferProcs /*{typ.name}*/_tp_as_buffer = {
    (getbufferproc)/*{ typ.bf_getbuffer or 0 }*/,
    (releasebufferproc)/*{ typ.bf_releasebuffer or 0 }*/,
};
//!
/// endif
PyTypeObject /*{typ.name}*/_Type = {
    PyVarObject_HEAD_INIT(0, 0)
    "/*{module}*/./*{typ.name}*/",
    sizeof(/*{typ.name}*/),
    0,
    (destructor)/*{ typ.tp_dealloc or 0 }*/,
    0,
    0,
    0,
    /*{ typ.tp_as_async or 0 }*/,
    (reprfunc)/*{ typ.tp_repr or 0 }*/,
    /*{ typ.tp_as_number or 0 }*/,
    /*{ typ.tp_as_sequence or 0 }*/,
    /*{ typ.tp_as_mapping or 0 }*/,
    (hashfunc)/*{ typ.tp_hash or 0 }*/,
    (ternaryfunc)/*{ typ.tp_call or 0 }*/,
    (reprfunc)/*{ typ.tp_reprfunc or 0 }*/,
    (getattrofunc)/*{ typ.tp_getattro or 0 }*/,
    (setattrofunc)/*{ typ.tp_setattro or 0 }*/,
    /*{ typ.tp_as_buffer or 0 }*/,
    Py_TPFLAGS_DEFAULT,
    "/*{module}*/./*{typ.name}*/",
    (traverseproc)/*{ typ.tp_traverse or 0 }*/,
    (inquiry)/*{ typ.tp_clear or 0 }*/,
    (richcmpfunc)/*{ typ.tp_richcompare or 0 }*/,
    0,
    (getiterfunc)/*{ typ.tp_iter or 0 }*/,
    (iternextfunc)/*{ typ.tp_iternext or 0 }*/,
    /*{ typ.tp_methods or 0 }*/,
    0,
    /*{ typ.tp_getset or 0 }*/,
    /*{ typ.tp_base or 0 }*/,
    0,
    0,
    0,
    0,
    (initproc)/*{ typ.tp_init or 0 }*/,
    (allocfunc)/*{ typ.tp_alloc or 0 }*/,
    (newfunc)/*{ typ.tp_new or 0 }*/,
    (freefunc)/*{ typ.tp_free or 0 }*/,
    0,
    0,
    0,
    0,
    0,
    0,
    (destructor)/*{ typ.tp_del or 0 }*/,
    0,
    0,
};
//!
/// endfor
//!
'''

module_template = '''\
#include <Python.h>
//!
/// if types
/// for typ in types.values()
extern PyTypeObject /*{typ.name}*/_Type;
/// endfor
//!
/// endif
/// if methods
/// for meth in methods.values()
extern PyCFunction __meth_/*{meth.name}*/;
/// endfor
//!
/// endif
PyMethodDef module_methods[] = {
/// for meth in methods.values()
    {"/*{meth.name}*/", __meth_/*{meth.name}*/, /*{meth.flags}*/, 0},
/// endfor
    {0, 0, 0, 0},
};
//!
PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "/*{module}*/",
    0,
    -1,
    module_methods,
    0,
    0,
    0,
    0,
};
//!
extern "C" PyObject * PyInit_/*{module}*/() {
    PyObject * module = PyModule_Create(&module_def);
//!
    if (!module) {
      return module;
    }
//!
/// for typ in types.values()
    if (PyType_Ready(&/*{typ.name}*/_Type) < 0) {
        PyErr_Format(PyExc_ImportError, "Cannot register /*{typ.name}*/");
        return 0;
    }
//!
    Py_INCREF(&/*{typ.name}*/_Type);
    PyModule_AddObject(module, "/*{typ.name}*/", (PyObject *)&/*{typ.name}*/_Type);
//!
/// endfor
    return module;
}
//!
'''
