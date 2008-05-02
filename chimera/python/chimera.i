%module chimera
%{
#include "chimera.h"
%}

%include "swigpyrun.h"
%include "chimera.h"
%include "key.h"
%include "log.h"
%include "host.h"

// Type mapping for grabbing a FILE * from Python
%typemap(in) FILE* {
  if (!PyFile_Check($input)) {
      PyErr_SetString(PyExc_TypeError, "Need a file!");
      return NULL;
  }
  $1 = PyFile_AsFile($input);
}

%typemap(in) chimera_update_upcall_t{
    if(!PyCallable_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "Need a callable object")
        return NULL;
    }
    pyupdatecb = *func;
    $1 = PythonUpdateCB;
}

%{
    PyObject *pyupdatecb, *pyforwardcb, *pydelivercb;

    /* Callback functions that need to go up into python */
    void PythonForwardCB (Key ** k, Message **m, ChimeraHost **h)
    {
        PyObject *arglist;
        PyObject *result;
        if (SWIG_ConvertPtr($input, void(**) &$1, $1_descriptor) == -1) 
            return NULL;
        if (SWIG_ConvertPtr($input, void(**) &$2, $2_descriptor) == -1) 
            return NULL;
        if (SWIG_ConvertPtr($input, void(**) &$3, $3_descriptor) == -1) 
            return NULL;

        arglist = Py_BuildValue("(OOO)", k, m, h);
        result = PyEval_CallObject(pyforwardcb, arglist);
        Py_DECREF(arglist);
        Py_XDECREF(result);
    }

    void PythonUpdateCB (Key *k, ChimeraHost *h, int joined)
    {
        PyObject *arglist;
        PyObject *result;
        if (SWIG_ConvertPtr($input, void(**) &$1, $1_descriptor) == -1) 
            return NULL;
        if (SWIG_ConvertPtr($input, void(**) &$2, $2_descriptor) == -1) 
            return NULL;

        arglist = Py_BuildValue("(OOi)", k, h, joined);
        result = PyEval_CallObject(pyupdatecb, arglist);
        Py_DECREF(arglist);
        Py_XDECREF(result);
    }
%}
