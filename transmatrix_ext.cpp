#ifdef __CPLUSPLUS__
extern "C" {
#endif

#ifndef __GNUC__
#pragma warning(disable: 4275)
#pragma warning(disable: 4101)

#endif
#include "Python.h"
#include "blitz/array.h"
#include "compile.h"
#include "frameobject.h"
#include <complex>
#include <math.h>
#include <string>
#include "scxx/object.h"
#include "scxx/list.h"
#include "scxx/tuple.h"
#include "scxx/dict.h"
#include <iostream>
#include <stdio.h>
#include "numpy/arrayobject.h"




// global None value for use in functions.
namespace py {
object None = object(Py_None);
}

const char* find_type(PyObject* py_obj)
{
    if(py_obj == NULL) return "C NULL value";
    if(PyCallable_Check(py_obj)) return "callable";
    if(PyString_Check(py_obj)) return "string";
    if(PyInt_Check(py_obj)) return "int";
    if(PyFloat_Check(py_obj)) return "float";
    if(PyDict_Check(py_obj)) return "dict";
    if(PyList_Check(py_obj)) return "list";
    if(PyTuple_Check(py_obj)) return "tuple";
    if(PyFile_Check(py_obj)) return "file";
    if(PyModule_Check(py_obj)) return "module";

    //should probably do more intergation (and thinking) on these.
    if(PyCallable_Check(py_obj) && PyInstance_Check(py_obj)) return "callable";
    if(PyInstance_Check(py_obj)) return "instance";
    if(PyCallable_Check(py_obj)) return "callable";
    return "unkown type";
}

void throw_error(PyObject* exc, const char* msg)
{
 //printf("setting python error: %s\n",msg);
  PyErr_SetString(exc, msg);
  //printf("throwing error\n");
  throw 1;
}

void handle_bad_type(PyObject* py_obj, const char* good_type, const char* var_name)
{
    char msg[500];
    sprintf(msg,"received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);
}

void handle_conversion_error(PyObject* py_obj, const char* good_type, const char* var_name)
{
    char msg[500];
    sprintf(msg,"Conversion Error:, received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);
}


class int_handler
{
public:
    int convert_to_int(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyInt_Check(py_obj))
            handle_conversion_error(py_obj,"int", name);
        return (int) PyInt_AsLong(py_obj);
    }

    int py_to_int(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyInt_Check(py_obj))
            handle_bad_type(py_obj,"int", name);
        
        return (int) PyInt_AsLong(py_obj);
    }
};

int_handler x__int_handler = int_handler();
#define convert_to_int(py_obj,name) \
        x__int_handler.convert_to_int(py_obj,name)
#define py_to_int(py_obj,name) \
        x__int_handler.py_to_int(py_obj,name)


PyObject* int_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class float_handler
{
public:
    double convert_to_float(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyFloat_Check(py_obj))
            handle_conversion_error(py_obj,"float", name);
        return PyFloat_AsDouble(py_obj);
    }

    double py_to_float(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyFloat_Check(py_obj))
            handle_bad_type(py_obj,"float", name);
        
        return PyFloat_AsDouble(py_obj);
    }
};

float_handler x__float_handler = float_handler();
#define convert_to_float(py_obj,name) \
        x__float_handler.convert_to_float(py_obj,name)
#define py_to_float(py_obj,name) \
        x__float_handler.py_to_float(py_obj,name)


PyObject* float_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class complex_handler
{
public:
    std::complex<double> convert_to_complex(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyComplex_Check(py_obj))
            handle_conversion_error(py_obj,"complex", name);
        return std::complex<double>(PyComplex_RealAsDouble(py_obj),PyComplex_ImagAsDouble(py_obj));
    }

    std::complex<double> py_to_complex(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyComplex_Check(py_obj))
            handle_bad_type(py_obj,"complex", name);
        
        return std::complex<double>(PyComplex_RealAsDouble(py_obj),PyComplex_ImagAsDouble(py_obj));
    }
};

complex_handler x__complex_handler = complex_handler();
#define convert_to_complex(py_obj,name) \
        x__complex_handler.convert_to_complex(py_obj,name)
#define py_to_complex(py_obj,name) \
        x__complex_handler.py_to_complex(py_obj,name)


PyObject* complex_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class unicode_handler
{
public:
    Py_UNICODE* convert_to_unicode(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyUnicode_Check(py_obj))
            handle_conversion_error(py_obj,"unicode", name);
        return PyUnicode_AS_UNICODE(py_obj);
    }

    Py_UNICODE* py_to_unicode(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyUnicode_Check(py_obj))
            handle_bad_type(py_obj,"unicode", name);
        Py_XINCREF(py_obj);
        return PyUnicode_AS_UNICODE(py_obj);
    }
};

unicode_handler x__unicode_handler = unicode_handler();
#define convert_to_unicode(py_obj,name) \
        x__unicode_handler.convert_to_unicode(py_obj,name)
#define py_to_unicode(py_obj,name) \
        x__unicode_handler.py_to_unicode(py_obj,name)


PyObject* unicode_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class string_handler
{
public:
    std::string convert_to_string(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyString_Check(py_obj))
            handle_conversion_error(py_obj,"string", name);
        return std::string(PyString_AsString(py_obj));
    }

    std::string py_to_string(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyString_Check(py_obj))
            handle_bad_type(py_obj,"string", name);
        Py_XINCREF(py_obj);
        return std::string(PyString_AsString(py_obj));
    }
};

string_handler x__string_handler = string_handler();
#define convert_to_string(py_obj,name) \
        x__string_handler.convert_to_string(py_obj,name)
#define py_to_string(py_obj,name) \
        x__string_handler.py_to_string(py_obj,name)


               PyObject* string_to_py(std::string s)
               {
                   return PyString_FromString(s.c_str());
               }
               
class list_handler
{
public:
    py::list convert_to_list(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyList_Check(py_obj))
            handle_conversion_error(py_obj,"list", name);
        return py::list(py_obj);
    }

    py::list py_to_list(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyList_Check(py_obj))
            handle_bad_type(py_obj,"list", name);
        
        return py::list(py_obj);
    }
};

list_handler x__list_handler = list_handler();
#define convert_to_list(py_obj,name) \
        x__list_handler.convert_to_list(py_obj,name)
#define py_to_list(py_obj,name) \
        x__list_handler.py_to_list(py_obj,name)


PyObject* list_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class dict_handler
{
public:
    py::dict convert_to_dict(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyDict_Check(py_obj))
            handle_conversion_error(py_obj,"dict", name);
        return py::dict(py_obj);
    }

    py::dict py_to_dict(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyDict_Check(py_obj))
            handle_bad_type(py_obj,"dict", name);
        
        return py::dict(py_obj);
    }
};

dict_handler x__dict_handler = dict_handler();
#define convert_to_dict(py_obj,name) \
        x__dict_handler.convert_to_dict(py_obj,name)
#define py_to_dict(py_obj,name) \
        x__dict_handler.py_to_dict(py_obj,name)


PyObject* dict_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class tuple_handler
{
public:
    py::tuple convert_to_tuple(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyTuple_Check(py_obj))
            handle_conversion_error(py_obj,"tuple", name);
        return py::tuple(py_obj);
    }

    py::tuple py_to_tuple(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyTuple_Check(py_obj))
            handle_bad_type(py_obj,"tuple", name);
        
        return py::tuple(py_obj);
    }
};

tuple_handler x__tuple_handler = tuple_handler();
#define convert_to_tuple(py_obj,name) \
        x__tuple_handler.convert_to_tuple(py_obj,name)
#define py_to_tuple(py_obj,name) \
        x__tuple_handler.py_to_tuple(py_obj,name)


PyObject* tuple_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class file_handler
{
public:
    FILE* convert_to_file(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyFile_Check(py_obj))
            handle_conversion_error(py_obj,"file", name);
        return PyFile_AsFile(py_obj);
    }

    FILE* py_to_file(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyFile_Check(py_obj))
            handle_bad_type(py_obj,"file", name);
        Py_XINCREF(py_obj);
        return PyFile_AsFile(py_obj);
    }
};

file_handler x__file_handler = file_handler();
#define convert_to_file(py_obj,name) \
        x__file_handler.convert_to_file(py_obj,name)
#define py_to_file(py_obj,name) \
        x__file_handler.py_to_file(py_obj,name)


               PyObject* file_to_py(FILE* file, char* name, char* mode)
               {
                   return (PyObject*) PyFile_FromFile(file, name, mode, fclose);
               }
               
class instance_handler
{
public:
    py::object convert_to_instance(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyInstance_Check(py_obj))
            handle_conversion_error(py_obj,"instance", name);
        return py::object(py_obj);
    }

    py::object py_to_instance(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyInstance_Check(py_obj))
            handle_bad_type(py_obj,"instance", name);
        
        return py::object(py_obj);
    }
};

instance_handler x__instance_handler = instance_handler();
#define convert_to_instance(py_obj,name) \
        x__instance_handler.convert_to_instance(py_obj,name)
#define py_to_instance(py_obj,name) \
        x__instance_handler.py_to_instance(py_obj,name)


PyObject* instance_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class numpy_size_handler
{
public:
    void conversion_numpy_check_size(PyArrayObject* arr_obj, int Ndims,
                                     const char* name)
    {
        if (arr_obj->nd != Ndims)
        {
            char msg[500];
            sprintf(msg,"Conversion Error: received '%d' dimensional array instead of '%d' dimensional array for variable '%s'",
                    arr_obj->nd,Ndims,name);
            throw_error(PyExc_TypeError,msg);
        }
    }

    void numpy_check_size(PyArrayObject* arr_obj, int Ndims, const char* name)
    {
        if (arr_obj->nd != Ndims)
        {
            char msg[500];
            sprintf(msg,"received '%d' dimensional array instead of '%d' dimensional array for variable '%s'",
                    arr_obj->nd,Ndims,name);
            throw_error(PyExc_TypeError,msg);
        }
    }
};

numpy_size_handler x__numpy_size_handler = numpy_size_handler();
#define conversion_numpy_check_size x__numpy_size_handler.conversion_numpy_check_size
#define numpy_check_size x__numpy_size_handler.numpy_check_size


class numpy_type_handler
{
public:
    void conversion_numpy_check_type(PyArrayObject* arr_obj, int numeric_type,
                                     const char* name)
    {
        // Make sure input has correct numeric type.
        int arr_type = arr_obj->descr->type_num;
        if (PyTypeNum_ISEXTENDED(numeric_type))
        {
        char msg[80];
        sprintf(msg, "Conversion Error: extended types not supported for variable '%s'",
                name);
        throw_error(PyExc_TypeError, msg);
        }
        if (!PyArray_EquivTypenums(arr_type, numeric_type))
        {

        const char* type_names[23] = {"bool", "byte", "ubyte","short", "ushort",
                                "int", "uint", "long", "ulong", "longlong", "ulonglong",
                                "float", "double", "longdouble", "cfloat", "cdouble",
                                "clongdouble", "object", "string", "unicode", "void", "ntype",
                                "unknown"};
        char msg[500];
        sprintf(msg,"Conversion Error: received '%s' typed array instead of '%s' typed array for variable '%s'",
                type_names[arr_type],type_names[numeric_type],name);
        throw_error(PyExc_TypeError,msg);
        }
    }

    void numpy_check_type(PyArrayObject* arr_obj, int numeric_type, const char* name)
    {
        // Make sure input has correct numeric type.
        int arr_type = arr_obj->descr->type_num;
        if (PyTypeNum_ISEXTENDED(numeric_type))
        {
        char msg[80];
        sprintf(msg, "Conversion Error: extended types not supported for variable '%s'",
                name);
        throw_error(PyExc_TypeError, msg);
        }
        if (!PyArray_EquivTypenums(arr_type, numeric_type))
        {
            const char* type_names[23] = {"bool", "byte", "ubyte","short", "ushort",
                                    "int", "uint", "long", "ulong", "longlong", "ulonglong",
                                    "float", "double", "longdouble", "cfloat", "cdouble",
                                    "clongdouble", "object", "string", "unicode", "void", "ntype",
                                    "unknown"};
            char msg[500];
            sprintf(msg,"received '%s' typed array instead of '%s' typed array for variable '%s'",
                    type_names[arr_type],type_names[numeric_type],name);
            throw_error(PyExc_TypeError,msg);
        }
    }
};

numpy_type_handler x__numpy_type_handler = numpy_type_handler();
#define conversion_numpy_check_type x__numpy_type_handler.conversion_numpy_check_type
#define numpy_check_type x__numpy_type_handler.numpy_check_type


class numpy_handler
{
public:
    PyArrayObject* convert_to_numpy(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyArray_Check(py_obj))
            handle_conversion_error(py_obj,"numpy", name);
        return (PyArrayObject*) py_obj;
    }

    PyArrayObject* py_to_numpy(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyArray_Check(py_obj))
            handle_bad_type(py_obj,"numpy", name);
        Py_XINCREF(py_obj);
        return (PyArrayObject*) py_obj;
    }
};

numpy_handler x__numpy_handler = numpy_handler();
#define convert_to_numpy(py_obj,name) \
        x__numpy_handler.convert_to_numpy(py_obj,name)
#define py_to_numpy(py_obj,name) \
        x__numpy_handler.py_to_numpy(py_obj,name)


PyObject* numpy_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class catchall_handler
{
public:
    py::object convert_to_catchall(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !(py_obj))
            handle_conversion_error(py_obj,"catchall", name);
        return py::object(py_obj);
    }

    py::object py_to_catchall(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !(py_obj))
            handle_bad_type(py_obj,"catchall", name);
        
        return py::object(py_obj);
    }
};

catchall_handler x__catchall_handler = catchall_handler();
#define convert_to_catchall(py_obj,name) \
        x__catchall_handler.convert_to_catchall(py_obj,name)
#define py_to_catchall(py_obj,name) \
        x__catchall_handler.py_to_catchall(py_obj,name)


PyObject* catchall_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}



// This should be declared only if they are used by some function
// to keep from generating needless warnings. for now, we'll always
// declare them.

int _beg = blitz::fromStart;
int _end = blitz::toEnd;
blitz::Range _all = blitz::Range::all();

template<class T, int N>
static blitz::Array<T,N> convert_to_blitz(PyArrayObject* arr_obj,const char* name)
{
    blitz::TinyVector<int,N> shape(0);
    blitz::TinyVector<int,N> strides(0);
    //for (int i = N-1; i >=0; i--)
    for (int i = 0; i < N; i++)
    {
        shape[i] = arr_obj->dimensions[i];
        strides[i] = arr_obj->strides[i]/sizeof(T);
    }
    //return blitz::Array<T,N>((T*) arr_obj->data,shape,
    return blitz::Array<T,N>((T*) arr_obj->data,shape,strides,
                             blitz::neverDeleteData);
}

template<class T, int N>
static blitz::Array<T,N> py_to_blitz(PyArrayObject* arr_obj,const char* name)
{

    blitz::TinyVector<int,N> shape(0);
    blitz::TinyVector<int,N> strides(0);
    //for (int i = N-1; i >=0; i--)
    for (int i = 0; i < N; i++)
    {
        shape[i] = arr_obj->dimensions[i];
        strides[i] = arr_obj->strides[i]/sizeof(T);
    }
    //return blitz::Array<T,N>((T*) arr_obj->data,shape,
    return blitz::Array<T,N>((T*) arr_obj->data,shape,strides,
                             blitz::neverDeleteData);
}


static PyObject* trans_matrix(PyObject*self, PyObject* args, PyObject* kywds)
{
    py::object return_val;
    int exception_occured = 0;
    PyObject *py_local_dict = NULL;
    static char *kwlist[] = {"qlen","rlen","T","r","q","c","local_dict", NULL};
    PyObject *py_qlen, *py_rlen, *py_T, *py_r, *py_q, *py_c;
    int qlen_used, rlen_used, T_used, r_used, q_used, c_used;
    py_qlen = py_rlen = py_T = py_r = py_q = py_c = NULL;
    qlen_used= rlen_used= T_used= r_used= q_used= c_used = 0;
    
    if(!PyArg_ParseTupleAndKeywords(args,kywds,"OOOOOO|O:trans_matrix",kwlist,&py_qlen, &py_rlen, &py_T, &py_r, &py_q, &py_c, &py_local_dict))
       return NULL;
    try                              
    {                                
        py_qlen = py_qlen;
        int qlen = convert_to_int(py_qlen,"qlen");
        qlen_used = 1;
        py_rlen = py_rlen;
        int rlen = convert_to_int(py_rlen,"rlen");
        rlen_used = 1;
        py_T = py_T;
        PyArrayObject* T_array = convert_to_numpy(py_T,"T");
        conversion_numpy_check_type(T_array,PyArray_DOUBLE,"T");
        conversion_numpy_check_size(T_array,2,"T");
        blitz::Array<double,2> T = convert_to_blitz<double,2>(T_array,"T");
        blitz::TinyVector<int,2> NT = T.shape();
        T_used = 1;
        py_r = py_r;
        PyArrayObject* r_array = convert_to_numpy(py_r,"r");
        conversion_numpy_check_type(r_array,PyArray_DOUBLE,"r");
        conversion_numpy_check_size(r_array,1,"r");
        blitz::Array<double,1> r = convert_to_blitz<double,1>(r_array,"r");
        blitz::TinyVector<int,1> Nr = r.shape();
        r_used = 1;
        py_q = py_q;
        PyArrayObject* q_array = convert_to_numpy(py_q,"q");
        conversion_numpy_check_type(q_array,PyArray_DOUBLE,"q");
        conversion_numpy_check_size(q_array,1,"q");
        blitz::Array<double,1> q = convert_to_blitz<double,1>(q_array,"q");
        blitz::TinyVector<int,1> Nq = q.shape();
        q_used = 1;
        py_c = py_c;
        int c = convert_to_int(py_c,"c");
        c_used = 1;
        /*<function call here>*/     
        
            
            float chk, qr;
            int i, j;
            
            for( i = 0; i < qlen; i++)
                   for( j = 0; j < rlen; j++)
                   {
                         
                         qr = q(i) * r(j);
                         chk = float(c) * sin(qr) / qr ;
        
                          if(chk != chk) {
                              T(i,j) = 1;
                          }
                          else {
                              T(i,j) = chk; 
                          }
                              
                   }
                   
        if(py_local_dict)                                  
        {                                                  
            py::dict local_dict = py::dict(py_local_dict); 
        }                                                  
    
    }                                
    catch(...)                       
    {                                
        return_val =  py::object();      
        exception_occured = 1;       
    }                                
    /*cleanup code*/                     
    if(T_used)
    {
        Py_XDECREF(py_T);
    }
    if(r_used)
    {
        Py_XDECREF(py_r);
    }
    if(q_used)
    {
        Py_XDECREF(py_q);
    }
    if(!(PyObject*)return_val && !exception_occured)
    {
                                  
        return_val = Py_None;            
    }
                                  
    return return_val.disown();           
}                                


static PyMethodDef compiled_methods[] = 
{
    {"trans_matrix",(PyCFunction)trans_matrix , METH_VARARGS|METH_KEYWORDS},
    {NULL,      NULL}        /* Sentinel */
};

PyMODINIT_FUNC inittransmatrix_ext(void)
{
    
    Py_Initialize();
    import_array();
    PyImport_ImportModule("numpy");
    (void) Py_InitModule("transmatrix_ext", compiled_methods);
}

#ifdef __CPLUSCPLUS__
}
#endif
