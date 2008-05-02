/* ****
 * An extension to stackless that distributes tasklets over a network
 *
 * Justin Tulloss
 * 04/19/08 - Began writing
 * 04/23/2008 - Starting over with just accessor functions here and most of the
 *              work done in python
 */

#include <Python.h>
#include <chimera.h>

/* Message Types */
#define TASK_NEW 15
#define TASK_OP 16
#define CH_SUBSCRIBE 17
#define CH_UNSUBSCRIBE 18
#define CH_PUBLISH 19
#define CH_NEW 20
#define CH_BROADCAST 21
#define CH_DELIVERED 22

/* Declare stuff */
static PyObject* init_network(PyObject *self, PyObject *args);

static PyObject* send(PyObject *self, PyObject *args);

static PyObject* set_update(PyObject *self, PyObject *args);
static PyObject* set_deliver(PyObject *self, PyObject *args);
static PyObject* set_forward(PyObject *self, PyObject *args);

static void handle_update(Key *key, ChimeraHost *host, int joined);
static void handle_deliver(Key *key, Message *msg);
static void handle_forward(Key **key, Message **msg, ChimeraHost **host);

static PyObject* make_key(PyObject *self, PyObject *args);

static PyObject * _fill_func(PyObject **fxnptr, PyObject *args);

typedef struct {
    ChimeraState *chimera;
    PyObject *update;
    PyObject *deliver;
    PyObject *forward;
} NetworkBase;

NetworkBase netstate;
static int hashcount = 0; /* An effort to keep the hashes different*/

static PyObject *
init_network(PyObject *self, PyObject *args)
{
    char *bootstrap = NULL;
    ChimeraHost *host = NULL;
    ChimeraState *c;
    int port;

    /* To Be Safe...*/
    PyEval_InitThreads();

    if (!PyArg_ParseTuple(args, "i|s", &port, &bootstrap))
        return NULL;

    /* Initialize the network, with bootstrap if we got one */
    netstate.chimera = chimera_init(port);
    c = netstate.chimera;

    if (bootstrap != NULL) {
        host = host_decode(c, bootstrap);
        chimera_join(c, host);
        host_release(c, host);
    }
    else {
        chimera_join(c, NULL);
    }

    /* Register our messages */
    chimera_register(c, TASK_NEW, 1);
    chimera_register(c, TASK_OP, 1);
    chimera_register(c, CH_SUBSCRIBE, 1);
    chimera_register(c, CH_UNSUBSCRIBE, 1);
    chimera_register(c, CH_PUBLISH, 1);
    chimera_register(c, CH_NEW, 1);
    chimera_register(c, CH_BROADCAST, 1);
    chimera_register(c, CH_DELIVERED, 1);

    /* Register our callbacks */
    chimera_update(c, handle_update);
    chimera_deliver(c, handle_deliver);
    chimera_forward(c, handle_forward);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
send (PyObject *self, PyObject* args)
{
    char *keystr;
    int type;
    char *msg;

    Key key;

    if (!PyArg_ParseTuple(args, "sis", &keystr, &type, &msg))
        return NULL;

    str_to_key(keystr, &key);
    chimera_send(netstate.chimera, key, type, strlen(msg), msg);

    Py_RETURN_NONE;
}

static void
handle_update(Key *key, ChimeraHost *host, int joined)
{
    PyObject *args;
    PyGILState_STATE gstate;

    if (netstate.update) {
        gstate = PyGILState_Ensure();

        /* Build Args */
        args = Py_BuildValue("ssi", key->keystr, host->name, joined);

        /* Call Python function */
        PyEval_CallObject(netstate.update, args);
        Py_DECREF(args);

        PyGILState_Release(gstate);
    }
}

static void
handle_deliver(Key *key, Message *msg)
{
    PyObject *args;
    PyGILState_STATE gstate;

    if (netstate.deliver) {
        gstate = PyGILState_Ensure();

        /* Build Args */
        args = Py_BuildValue("sis#", 
            key->keystr, 
            msg->type, 
            msg->payload, 
            msg->size
        );

        /* Call Python function */
        PyEval_CallObject(netstate.deliver, args);
        Py_DECREF(args);

        PyGILState_Release(gstate);
    }
}

static void
handle_forward(Key **key, Message **msg, ChimeraHost **host)
{
    /* Not Implemented Yet (I don't care) */
}

static PyObject * 
set_update(PyObject *self, PyObject *args)
{
    return _fill_func(&netstate.update, args);
}

static PyObject * 
set_deliver(PyObject *self, PyObject *args)
{
    return _fill_func(&netstate.deliver, args);
}

static PyObject * 
set_forward(PyObject *self, PyObject *args)
{
    /*return _fill_func(&netstate.forward, args);*/
    PyErr_SetString(PyExc_NotImplementedError, "Can't handle forwarding yet");
    return NULL;
}

static PyObject* 
make_key(PyObject *self, PyObject *args)
{
    Key newkey;
    long hash;
    int seed = 1;
    PyObject *obj;
    PyObject *hashstr;

    if (!PyArg_ParseTuple(args, "O|i", &obj, &seed))
        return NULL;
        
    hash = PyObject_Hash(obj);
    if (hash == -1) {
        PyErr_SetString(PyExc_Exception, "Could not hash object");
        return NULL;
    }

    if (seed) {
        hashcount++;
        hashstr = PyString_FromFormat("%ld%d", hash, hashcount);
    }
    else
        hashstr = PyString_FromFormat("%ld", hash);


    key_make_hash(&newkey, PyString_AsString(hashstr), PyString_Size(hashstr));

    return Py_BuildValue("s", newkey.keystr);
}

static PyObject *
get_node_key(PyObject *self)
{
    ChimeraGlobal *glbl = (ChimeraGlobal *)netstate.chimera->chimera;

    return PyString_FromFormat("%s", glbl->me->key.keystr);
}


/* Internal Helpers */
static PyObject *
_fill_func(PyObject **fxnptr, PyObject *args)
{
    PyObject *func = NULL;

    if (PyArg_ParseTuple(args, "O:callback", &func)){
        if (!PyCallable_Check(func)) {
            PyErr_SetString(PyExc_TypeError, "Parameter must be callable");
            return NULL;
        }
        Py_XINCREF(func);
        Py_XDECREF(*fxnptr);
        *fxnptr = func;
        Py_RETURN_NONE;
    }
    return NULL;
}

static PyMethodDef DstackBaseMethods[] = {
    {
        "init_network", (PyCFunction)init_network, METH_VARARGS,
        "Initialize the distributed network. Accepts a bootstrap or nothing."
    },
    {
        "send", (PyCFunction)send, METH_VARARGS,
        "Send a message through the network. Takes the key, type, and message"
    },
    {
        "set_update", (PyCFunction)set_update, METH_VARARGS,
        "Set the update function. Provide a python callable."
    },
    {
        "set_deliver", (PyCFunction)set_deliver, METH_VARARGS,
        "Set the deliver function. Provide a python callable."
    },
    {
        "set_forward", (PyCFunction)set_forward, METH_VARARGS,
        "Set the forward function. Provide a python callable."
    },
    {
        "make_key", (PyCFunction)make_key, METH_VARARGS,
        "Makes a chimera key for the object you give. Returns a string."
    },
    {
        "get_node_key", (PyCFunction)get_node_key, METH_NOARGS,
        "Returns the key for the currently running chimera node"
    },
    { NULL, NULL, 0, NULL } /* Sentinel */
};

PyMODINIT_FUNC
init_dstack(void)
{
    Py_InitModule("_dstack", DstackBaseMethods);
}
