
// Boost Includes ==============================================================
#include <boost/python.hpp>
#include <boost/cstdint.hpp>

// Includes ====================================================================
#include <emdata.h>
#include <emutil.h>
#include <imageio.h>
#include <sparx/SparxIO.h>
#include <testutil.h>
#include <util_wrapitems.h>
#include <xydata.h>

// Using =======================================================================
using namespace boost::python;

// Declarations ================================================================
namespace  {

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_Util_im_diff_overloads_2_3, EMAN::Util::im_diff, 2, 3)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_Util_TwoDTestFunc_overloads_5_7, EMAN::Util::TwoDTestFunc, 5, 7)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_Util_even_angles_overloads_1_5, EMAN::Util::even_angles, 1, 5)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_Util_decimate_overloads_2_4, EMAN::Util::decimate, 2, 4)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_Util_window_overloads_2_7, EMAN::Util::window, 2, 7)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_Util_pad_overloads_2_8, EMAN::Util::pad, 2, 8)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_Util_ctf_img_overloads_5_12, EMAN::Util::ctf_img, 5, 12)
struct EMAN_Util_KaiserBessel_Wrapper: EMAN::Util::KaiserBessel
{
    EMAN_Util_KaiserBessel_Wrapper(PyObject* py_self_, const EMAN::Util::KaiserBessel& p0):
        EMAN::Util::KaiserBessel(p0), py_self(py_self_) {}

    EMAN_Util_KaiserBessel_Wrapper(PyObject* py_self_, float p0, int p1, float p2, float p3, int p4):
        EMAN::Util::KaiserBessel(p0, p1, p2, p3, p4), py_self(py_self_) {}

    EMAN_Util_KaiserBessel_Wrapper(PyObject* py_self_, float p0, int p1, float p2, float p3, int p4, float p5):
        EMAN::Util::KaiserBessel(p0, p1, p2, p3, p4, p5), py_self(py_self_) {}

    EMAN_Util_KaiserBessel_Wrapper(PyObject* py_self_, float p0, int p1, float p2, float p3, int p4, float p5, int p6):
        EMAN::Util::KaiserBessel(p0, p1, p2, p3, p4, p5, p6), py_self(py_self_) {}

    void build_I0table() {
        call_method< void >(py_self, "build_I0table");
    }

    void default_build_I0table() {
        EMAN::Util::KaiserBessel::build_I0table();
    }

    float sinhwin(float p0) const {
        return call_method< float >(py_self, "sinhwin", p0);
    }

    float default_sinhwin(float p0) const {
        return EMAN::Util::KaiserBessel::sinhwin(p0);
    }

    float i0win(float p0) const {
        return call_method< float >(py_self, "i0win", p0);
    }

    float default_i0win(float p0) const {
        return EMAN::Util::KaiserBessel::i0win(p0);
    }

    PyObject* py_self;
};

struct EMAN_Util_FakeKaiserBessel_Wrapper: EMAN::Util::FakeKaiserBessel
{
    EMAN_Util_FakeKaiserBessel_Wrapper(PyObject* py_self_, const EMAN::Util::FakeKaiserBessel& p0):
        EMAN::Util::FakeKaiserBessel(p0), py_self(py_self_) {}

    EMAN_Util_FakeKaiserBessel_Wrapper(PyObject* py_self_, float p0, int p1, float p2, float p3, int p4):
        EMAN::Util::FakeKaiserBessel(p0, p1, p2, p3, p4), py_self(py_self_) {}

    EMAN_Util_FakeKaiserBessel_Wrapper(PyObject* py_self_, float p0, int p1, float p2, float p3, int p4, float p5):
        EMAN::Util::FakeKaiserBessel(p0, p1, p2, p3, p4, p5), py_self(py_self_) {}

    EMAN_Util_FakeKaiserBessel_Wrapper(PyObject* py_self_, float p0, int p1, float p2, float p3, int p4, float p5, int p6):
        EMAN::Util::FakeKaiserBessel(p0, p1, p2, p3, p4, p5, p6), py_self(py_self_) {}

    float sinhwin(float p0) const {
        return call_method< float >(py_self, "sinhwin", p0);
    }

    float default_sinhwin(float p0) const {
        return EMAN::Util::FakeKaiserBessel::sinhwin(p0);
    }

    float i0win(float p0) const {
        return call_method< float >(py_self, "i0win", p0);
    }

    float default_i0win(float p0) const {
        return EMAN::Util::FakeKaiserBessel::i0win(p0);
    }

    void build_I0table() {
        call_method< void >(py_self, "build_I0table");
    }

    void default_build_I0table() {
        EMAN::Util::FakeKaiserBessel::build_I0table();
    }

    PyObject* py_self;
};


BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_EMUtil_get_imageio_overloads_2_3, EMAN::EMUtil::get_imageio, 2, 3)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_TestUtil_check_image_overloads_1_2, EMAN::TestUtil::check_image, 1, 2)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_TestUtil_make_image_file_overloads_2_6, EMAN::TestUtil::make_image_file, 2, 6)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_TestUtil_verify_image_file_overloads_2_6, EMAN::TestUtil::verify_image_file, 2, 6)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_TestUtil_make_image_file2_overloads_2_6, EMAN::TestUtil::make_image_file2, 2, 6)

BOOST_PYTHON_FUNCTION_OVERLOADS(EMAN_TestUtil_verify_image_file2_overloads_2_6, EMAN::TestUtil::verify_image_file2, 2, 6)


}// namespace 


// Module ======================================================================
BOOST_PYTHON_MODULE(libpyUtils2)
{
    scope* EMAN_Util_scope = new scope(
    class_< EMAN::Util >("Util", init<  >())
        .def(init< const EMAN::Util& >())
        .def("coveig", &EMAN::Util::coveig)
        .def("ExpMinus4YSqr", &EMAN::Util::ExpMinus4YSqr)
        .def("WTM", &EMAN::Util::WTM)
        .def("WTF", &EMAN::Util::WTF)
        .def("CANG", &EMAN::Util::CANG)
        .def("BPCQ", &EMAN::Util::BPCQ)
        .def("infomask", &EMAN::Util::infomask)
        .def("cyclicshift", &EMAN::Util::cyclicshift)
        .def("im_diff", &EMAN::Util::im_diff, EMAN_Util_im_diff_overloads_2_3())
        .def("TwoDTestFunc", &EMAN::Util::TwoDTestFunc, EMAN_Util_TwoDTestFunc_overloads_5_7()[ return_value_policy< manage_new_object >() ])
        .def("splint", &EMAN::Util::splint)
        .def("even_angles", &EMAN::Util::even_angles, EMAN_Util_even_angles_overloads_1_5())
        .def("quadri", &EMAN::Util::quadri)
        .def("bilinear", &EMAN::Util::bilinear)
        .def("alrq", &EMAN::Util::alrq)
        .def("Polar2D", &EMAN::Util::Polar2D, return_value_policy< manage_new_object >())
        .def("Polar2Dm", &EMAN::Util::Polar2Dm, return_value_policy< manage_new_object >())
        .def("alrq_ms", &EMAN::Util::alrq_ms)
        .def("alrl_ms", &EMAN::Util::alrl_ms)
        .def("alrq_msi", &EMAN::Util::alrq_msi, return_value_policy< manage_new_object >())
        .def("Polar2Dmi", &EMAN::Util::Polar2Dmi, return_value_policy< manage_new_object >())
        .def("fftr_q", &EMAN::Util::fftr_q)
        .def("fftr_d", &EMAN::Util::fftr_d)
        .def("fftc_q", &EMAN::Util::fftc_q)
        .def("fftc_d", &EMAN::Util::fftc_d)
        .def("Frngs", &EMAN::Util::Frngs)
        .def("frngs", &EMAN::Util::frngs)
        .def("crosrng_e", &EMAN::Util::crosrng_e)
        .def("Crosrng_ms", &EMAN::Util::Crosrng_ms)
        .def("crosrng_ms", &EMAN::Util::crosrng_ms)
        .def("Crosrng_msr", &EMAN::Util::Crosrng_msr)
        .def("crosrng_msr", &EMAN::Util::crosrng_msr)
        .def("Crosrng_msg", &EMAN::Util::Crosrng_msg, return_value_policy< manage_new_object >())
        .def("crosrng_msg", &EMAN::Util::crosrng_msg)
        .def("prb1d", &EMAN::Util::prb1d)
        .def("decimate", &EMAN::Util::decimate, EMAN_Util_decimate_overloads_2_4()[ return_value_policy< manage_new_object >() ])
        .def("window", &EMAN::Util::window, EMAN_Util_window_overloads_2_7()[ return_value_policy< manage_new_object >() ])
        .def("pad", &EMAN::Util::pad, EMAN_Util_pad_overloads_2_8()[ return_value_policy< manage_new_object >() ])
        .def("histc", &EMAN::Util::histc)
        .def("hist_comp_freq", &EMAN::Util::hist_comp_freq)
        .def("ctf_img", &EMAN::Util::ctf_img, EMAN_Util_ctf_img_overloads_5_12()[ return_value_policy< manage_new_object >() ])
        .def("tf", &EMAN::Util::tf)
        .def("compress_image_mask", &EMAN::Util::compress_image_mask, return_value_policy< manage_new_object >())
        .def("reconstitute_image_mask", &EMAN::Util::reconstitute_image_mask, return_value_policy< manage_new_object >())
        .def("pw_extract", &EMAN::Util::pw_extract)
        .def("eval", &EMAN::Util::eval)
        .def("vrdg", &EMAN::Util::vrdg)
        .def("cmp1", &EMAN::Util::cmp1)
        .def("cmp2", &EMAN::Util::cmp2)
        .def("areav_", &EMAN::Util::areav_)
        .def("mult_scalar", &EMAN::Util::mult_scalar, return_value_policy< manage_new_object >())
        .def("mad_scalar", &EMAN::Util::mad_scalar, return_value_policy< manage_new_object >())
        .def("is_file_exist", &EMAN::Util::is_file_exist)
        .def("svdcmp", &EMAN::Util::svdcmp)
        .def("sstrncmp", &EMAN::Util::sstrncmp)
        .def("int2str", &EMAN::Util::int2str)
        .def("change_filename_ext", &EMAN::Util::change_filename_ext)
        .def("remove_filename_ext", &EMAN::Util::remove_filename_ext)
        .def("get_filename_ext", &EMAN::Util::get_filename_ext)
        .def("sbasename", &EMAN::Util::sbasename)
        .def("get_frand", (float (*)(int, int))&EMAN::Util::get_frand)
        .def("get_frand", (float (*)(float, float))&EMAN::Util::get_frand)
        .def("get_frand", (float (*)(double, double))&EMAN::Util::get_frand)
        .def("get_gauss_rand", &EMAN::Util::get_gauss_rand)
        .def("round", (int (*)(float))&EMAN::Util::round)
        .def("round", (int (*)(double))&EMAN::Util::round)
        .def("bilinear_interpolate", &EMAN::Util::bilinear_interpolate)
        .def("trilinear_interpolate", &EMAN::Util::trilinear_interpolate)
        .def("calc_best_fft_size", &EMAN::Util::calc_best_fft_size)
        .def("square", (int (*)(int))&EMAN::Util::square)
        .def("square", (float (*)(float))&EMAN::Util::square)
        .def("square", (float (*)(double))&EMAN::Util::square)
        .def("square_sum", &EMAN::Util::square_sum)
        .def("hypot3", (float (*)(int, int, int))&EMAN::Util::hypot3)
        .def("hypot3", (float (*)(float, float, float))&EMAN::Util::hypot3)
        .def("hypot3", (float (*)(double, double, double))&EMAN::Util::hypot3)
        .def("fast_floor", &EMAN::Util::fast_floor)
        .def("agauss", &EMAN::Util::agauss)
        .def("get_min", (int (*)(int, int))&EMAN::Util::get_min)
        .def("get_min", (int (*)(int, int, int))&EMAN::Util::get_min)
        .def("get_min", (float (*)(float, float))&EMAN::Util::get_min)
        .def("get_min", (float (*)(float, float, float))&EMAN::Util::get_min)
        .def("get_min", (float (*)(float, float, float, float))&EMAN::Util::get_min)
        .def("get_max", (float (*)(float, float))&EMAN::Util::get_max)
        .def("get_max", (float (*)(float, float, float))&EMAN::Util::get_max)
        .def("get_max", (float (*)(float, float, float, float))&EMAN::Util::get_max)
        .def("angle_sub_2pi", &EMAN::Util::angle_sub_2pi)
        .def("angle_sub_pi", &EMAN::Util::angle_sub_pi)
        .def("get_time_label", &EMAN::Util::get_time_label)
        .def("eman_copysign", &EMAN::Util::eman_copysign)
        .def("eman_erfc", &EMAN::Util::eman_erfc)
        .def("Crosrng_e", &util_Crosrng_e)
        .staticmethod("Crosrng_e")
        .staticmethod("alrq_ms")
        .staticmethod("CANG")
        .staticmethod("crosrng_ms")
        .staticmethod("areav_")
        .staticmethod("prb1d")
        .staticmethod("fftr_d")
        .staticmethod("TwoDTestFunc")
        .staticmethod("int2str")
        .staticmethod("splint")
        .staticmethod("crosrng_msg")
        .staticmethod("compress_image_mask")
        .staticmethod("calc_best_fft_size")
        .staticmethod("mad_scalar")
        .staticmethod("fftr_q")
        .staticmethod("BPCQ")
        .staticmethod("tf")
        .staticmethod("crosrng_msr")
        .staticmethod("reconstitute_image_mask")
        .staticmethod("change_filename_ext")
        .staticmethod("svdcmp")
        .staticmethod("vrdg")
        .staticmethod("bilinear")
        .staticmethod("Crosrng_ms")
        .staticmethod("is_file_exist")
        .staticmethod("fftc_d")
        .staticmethod("crosrng_e")
        .staticmethod("get_min")
        .staticmethod("Crosrng_msg")
        .staticmethod("alrl_ms")
        .staticmethod("cyclicshift")
        .staticmethod("window")
        .staticmethod("alrq_msi")
        .staticmethod("angle_sub_2pi")
        .staticmethod("WTF")
        .staticmethod("coveig")
        .staticmethod("Crosrng_msr")
        .staticmethod("pad")
        .staticmethod("pw_extract")
        .staticmethod("get_max")
        .staticmethod("ExpMinus4YSqr")
        .staticmethod("get_gauss_rand")
        .staticmethod("remove_filename_ext")
        .staticmethod("quadri")
        .staticmethod("fftc_q")
        .staticmethod("cmp2")
        .staticmethod("im_diff")
        .staticmethod("Polar2Dmi")
        .staticmethod("square")
        .staticmethod("hist_comp_freq")
        .staticmethod("square_sum")
        .staticmethod("even_angles")
        .staticmethod("trilinear_interpolate")
        .staticmethod("mult_scalar")
        .staticmethod("fast_floor")
        .staticmethod("Frngs")
        .staticmethod("get_time_label")
        .staticmethod("eval")
        .staticmethod("sstrncmp")
        .staticmethod("Polar2D")
        .staticmethod("agauss")
        .staticmethod("eman_erfc")
        .staticmethod("infomask")
        .staticmethod("bilinear_interpolate")
        .staticmethod("cmp1")
        .staticmethod("alrq")
        .staticmethod("WTM")
        .staticmethod("get_filename_ext")
        .staticmethod("frngs")
        .staticmethod("decimate")
        .staticmethod("get_frand")
        .staticmethod("hypot3")
        .staticmethod("angle_sub_pi")
        .staticmethod("histc")
        .staticmethod("eman_copysign")
        .staticmethod("sbasename")
        .staticmethod("round")
        .staticmethod("ctf_img")
        .staticmethod("Polar2Dm")
    );

    scope* EMAN_Util_KaiserBessel_scope = new scope(
    class_< EMAN::Util::KaiserBessel, EMAN_Util_KaiserBessel_Wrapper >("KaiserBessel", init< const EMAN::Util::KaiserBessel& >())
        .def(init< float, int, float, float, int, optional< float, int > >())
        .def("sinhwin", &EMAN::Util::KaiserBessel::sinhwin, &EMAN_Util_KaiserBessel_Wrapper::default_sinhwin)
        .def("i0win", &EMAN::Util::KaiserBessel::i0win, &EMAN_Util_KaiserBessel_Wrapper::default_i0win)
        .def("I0table_maxerror", &EMAN::Util::KaiserBessel::I0table_maxerror)
        .def("dump_table", &EMAN::Util::KaiserBessel::dump_table)
        .def("i0win_tab", &EMAN::Util::KaiserBessel::i0win_tab)
        .def("get_window_size", &EMAN::Util::KaiserBessel::get_window_size)
        .def("get_kbsinh_win", &EMAN::Util::KaiserBessel::get_kbsinh_win)
        .def("get_kbi0_win", &EMAN::Util::KaiserBessel::get_kbi0_win)
    );

    class_< EMAN::Util::KaiserBessel::kbsinh_win >("kbsinh_win", init< const EMAN::Util::KaiserBessel::kbsinh_win& >())
        .def(init< EMAN::Util::KaiserBessel& >())
        .def("get_window_size", &EMAN::Util::KaiserBessel::kbsinh_win::get_window_size)
        .def("__call__", &EMAN::Util::KaiserBessel::kbsinh_win::operator ())
    ;


    class_< EMAN::Util::KaiserBessel::kbi0_win >("kbi0_win", init< const EMAN::Util::KaiserBessel::kbi0_win& >())
        .def(init< EMAN::Util::KaiserBessel& >())
        .def("get_window_size", &EMAN::Util::KaiserBessel::kbi0_win::get_window_size)
        .def("__call__", &EMAN::Util::KaiserBessel::kbi0_win::operator ())
    ;

    delete EMAN_Util_KaiserBessel_scope;


    class_< EMAN::Util::FakeKaiserBessel, bases< EMAN::Util::KaiserBessel > , EMAN_Util_FakeKaiserBessel_Wrapper >("FakeKaiserBessel", init< const EMAN::Util::FakeKaiserBessel& >())
        .def(init< float, int, float, float, int, optional< float, int > >())
        .def("sinhwin", (float (EMAN::Util::FakeKaiserBessel::*)(float) const)&EMAN::Util::FakeKaiserBessel::sinhwin, (float (EMAN_Util_FakeKaiserBessel_Wrapper::*)(float) const)&EMAN_Util_FakeKaiserBessel_Wrapper::default_sinhwin)
        .def("i0win", (float (EMAN::Util::FakeKaiserBessel::*)(float) const)&EMAN::Util::FakeKaiserBessel::i0win, (float (EMAN_Util_FakeKaiserBessel_Wrapper::*)(float) const)&EMAN_Util_FakeKaiserBessel_Wrapper::default_i0win)
        .def("build_I0table", (void (EMAN::Util::FakeKaiserBessel::*)() )&EMAN::Util::FakeKaiserBessel::build_I0table, (void (EMAN_Util_FakeKaiserBessel_Wrapper::*)())&EMAN_Util_FakeKaiserBessel_Wrapper::default_build_I0table)
    ;


    class_< EMAN::Util::Gaussian >("Gaussian", init< const EMAN::Util::Gaussian& >())
        .def(init< optional< float > >())
        .def("__call__", &EMAN::Util::Gaussian::operator ())
    ;


    class_< EMAN::Util::tmpstruct >("tmpstruct", init<  >())
        .def(init< const EMAN::Util::tmpstruct& >())
        .def_readwrite("theta1", &EMAN::Util::tmpstruct::theta1)
        .def_readwrite("phi1", &EMAN::Util::tmpstruct::phi1)
        .def_readwrite("key1", &EMAN::Util::tmpstruct::key1)
    ;

    delete EMAN_Util_scope;

    scope* EMAN_EMUtil_scope = new scope(
    class_< EMAN::EMUtil >("EMUtil", init<  >())
        .def(init< const EMAN::EMUtil& >())
        .def("vertical_acf", &EMAN::EMUtil::vertical_acf, return_value_policy< manage_new_object >())
        .def("make_image_median", &EMAN::EMUtil::make_image_median, return_value_policy< manage_new_object >())
        .def("get_image_ext_type", &EMAN::EMUtil::get_image_ext_type)
        .def("get_image_type", &EMAN::EMUtil::get_image_type)
        .def("get_image_count", &EMAN::EMUtil::get_image_count)
        .def("get_imageio", &EMAN::EMUtil::get_imageio, EMAN_EMUtil_get_imageio_overloads_2_3()[ return_internal_reference< 1 >() ])
        .def("get_imagetype_name", &EMAN::EMUtil::get_imagetype_name)
        .def("get_datatype_string", &EMAN::EMUtil::get_datatype_string)
        .def("process_ascii_region_io", &EMAN::EMUtil::process_ascii_region_io)
        .def("dump_dict", &EMAN::EMUtil::dump_dict)
        .def("is_same_size", &EMAN::EMUtil::is_same_size)
        .def("is_same_ctf", &EMAN::EMUtil::is_same_ctf)
        .def("is_complex_type", &EMAN::EMUtil::is_complex_type)
        .def("jump_lines", &EMAN::EMUtil::jump_lines)
        .def("get_euler_names", &EMAN::EMUtil::get_euler_names)
        .def("get_all_attributes", &EMAN::EMUtil::get_all_attributes)
        .staticmethod("vertical_acf")
        .staticmethod("get_datatype_string")
        .staticmethod("dump_dict")
        .staticmethod("get_all_attributes")
        .staticmethod("get_imageio")
        .staticmethod("get_image_count")
        .staticmethod("get_imagetype_name")
        .staticmethod("get_image_type")
        .staticmethod("is_same_size")
        .staticmethod("make_image_median")
        .staticmethod("jump_lines")
        .staticmethod("get_euler_names")
        .staticmethod("is_same_ctf")
        .staticmethod("get_image_ext_type")
        .staticmethod("process_ascii_region_io")
        .staticmethod("is_complex_type")
    );

    enum_< EMAN::EMUtil::EMDataType >("EMDataType")
        .value("EM_SHORT_COMPLEX", EMAN::EMUtil::EM_SHORT_COMPLEX)
        .value("EM_SHORT", EMAN::EMUtil::EM_SHORT)
        .value("EM_UCHAR", EMAN::EMUtil::EM_UCHAR)
        .value("EM_FLOAT_COMPLEX", EMAN::EMUtil::EM_FLOAT_COMPLEX)
        .value("EM_CHAR", EMAN::EMUtil::EM_CHAR)
        .value("EM_INT", EMAN::EMUtil::EM_INT)
        .value("EM_USHORT", EMAN::EMUtil::EM_USHORT)
        .value("EM_USHORT_COMPLEX", EMAN::EMUtil::EM_USHORT_COMPLEX)
        .value("EM_UNKNOWN", EMAN::EMUtil::EM_UNKNOWN)
        .value("EM_UINT", EMAN::EMUtil::EM_UINT)
        .value("EM_DOUBLE", EMAN::EMUtil::EM_DOUBLE)
        .value("EM_FLOAT", EMAN::EMUtil::EM_FLOAT)
    ;


    enum_< EMAN::EMUtil::ImageType >("ImageType")
        .value("IMAGE_FITS", EMAN::EMUtil::IMAGE_FITS)
        .value("IMAGE_ICOS", EMAN::EMUtil::IMAGE_ICOS)
        .value("IMAGE_UNKNOWN", EMAN::EMUtil::IMAGE_UNKNOWN)
        .value("IMAGE_GATAN2", EMAN::EMUtil::IMAGE_GATAN2)
        .value("IMAGE_EMIM", EMAN::EMUtil::IMAGE_EMIM)
        .value("IMAGE_VTK", EMAN::EMUtil::IMAGE_VTK)
        .value("IMAGE_MRC", EMAN::EMUtil::IMAGE_MRC)
        .value("IMAGE_LST", EMAN::EMUtil::IMAGE_LST)
        .value("IMAGE_DM3", EMAN::EMUtil::IMAGE_DM3)
        .value("IMAGE_PNG", EMAN::EMUtil::IMAGE_PNG)
        .value("IMAGE_XPLOR", EMAN::EMUtil::IMAGE_XPLOR)
        .value("IMAGE_AMIRA", EMAN::EMUtil::IMAGE_AMIRA)
        .value("IMAGE_SAL", EMAN::EMUtil::IMAGE_SAL)
        .value("IMAGE_SPIDER", EMAN::EMUtil::IMAGE_SPIDER)
        .value("IMAGE_SINGLE_SPIDER", EMAN::EMUtil::IMAGE_SINGLE_SPIDER)
        .value("IMAGE_PGM", EMAN::EMUtil::IMAGE_PGM)
        .value("IMAGE_EM", EMAN::EMUtil::IMAGE_EM)
        .value("IMAGE_TIFF", EMAN::EMUtil::IMAGE_TIFF)
        .value("IMAGE_IMAGIC", EMAN::EMUtil::IMAGE_IMAGIC)
        .value("IMAGE_HDF", EMAN::EMUtil::IMAGE_HDF)
        .value("IMAGE_JPEG", EMAN::EMUtil::IMAGE_JPEG)
        .value("IMAGE_V4L", EMAN::EMUtil::IMAGE_V4L)
        .value("IMAGE_PIF", EMAN::EMUtil::IMAGE_PIF)
    ;

    delete EMAN_EMUtil_scope;

    class_< EMAN::ImageSort >("ImageSort", init< const EMAN::ImageSort& >())
        .def(init< int >())
        .def("sort", &EMAN::ImageSort::sort)
        .def("set", &EMAN::ImageSort::set)
        .def("get_index", &EMAN::ImageSort::get_index)
        .def("get_score", &EMAN::ImageSort::get_score)
        .def("size", &EMAN::ImageSort::size)
    ;

    class_< EMAN::TestUtil >("TestUtil", init<  >())
        .def(init< const EMAN::TestUtil& >())
        .def_readonly("EMDATA_HEADER_EXT", &EMAN::TestUtil::EMDATA_HEADER_EXT)
        .def_readonly("EMDATA_DATA_EXT", &EMAN::TestUtil::EMDATA_DATA_EXT)
        .def("get_debug_int", &EMAN::TestUtil::get_debug_int)
        .def("get_debug_float", &EMAN::TestUtil::get_debug_float)
        .def("get_debug_string", &EMAN::TestUtil::get_debug_string)
        .def("get_debug_image", &EMAN::TestUtil::get_debug_image)
        .def("get_golden_image", &EMAN::TestUtil::get_golden_image)
        .def("to_emobject", &EMAN::TestUtil::to_emobject)
        .def("emobject_to_py", (EMAN::EMObject (*)(int))&EMAN::TestUtil::emobject_to_py)
        .def("emobject_to_py", (EMAN::EMObject (*)(float))&EMAN::TestUtil::emobject_to_py)
        .def("emobject_to_py", (EMAN::EMObject (*)(double))&EMAN::TestUtil::emobject_to_py)
        .def("emobject_to_py", (EMAN::EMObject (*)(const std::string&))&EMAN::TestUtil::emobject_to_py)
        .def("emobject_to_py", (EMAN::EMObject (*)(EMAN::EMData*))&EMAN::TestUtil::emobject_to_py)
        .def("emobject_to_py", (EMAN::EMObject (*)(EMAN::XYData*))&EMAN::TestUtil::emobject_to_py)
        .def("emobject_farray_to_py", &EMAN::TestUtil::emobject_farray_to_py)
        .def("emobject_strarray_to_py", &EMAN::TestUtil::emobject_strarray_to_py)
        .def("test_IntPoint", &EMAN::TestUtil::test_IntPoint)
        .def("test_FloatPoint", &EMAN::TestUtil::test_FloatPoint)
        .def("test_IntSize", &EMAN::TestUtil::test_IntSize)
        .def("test_FloatSize", &EMAN::TestUtil::test_FloatSize)
        .def("test_Vec3i", &EMAN::TestUtil::test_Vec3i)
        .def("test_Vec3f", &EMAN::TestUtil::test_Vec3f)
        .def("test_vector_int", &EMAN::TestUtil::test_vector_int)
        .def("test_vector_float", &EMAN::TestUtil::test_vector_float)
        .def("test_vector_long", &EMAN::TestUtil::test_vector_long)
        .def("test_vector_string", &EMAN::TestUtil::test_vector_string)
        .def("test_vector_emdata", &EMAN::TestUtil::test_vector_emdata)
        .def("test_vector_pixel", &EMAN::TestUtil::test_vector_pixel)
        .def("test_map_int", &EMAN::TestUtil::test_map_int)
        .def("test_map_long", &EMAN::TestUtil::test_map_long)
        .def("test_map_float", &EMAN::TestUtil::test_map_float)
        .def("test_map_string", &EMAN::TestUtil::test_map_string)
        .def("test_map_emobject", &EMAN::TestUtil::test_map_emobject)
        .def("test_map_vecstring", &EMAN::TestUtil::test_map_vecstring)
        .def("test_dict", &EMAN::TestUtil::test_dict)
        .def("dump_image_from_file", &EMAN::TestUtil::dump_image_from_file)
        .def("dump_emdata", &EMAN::TestUtil::dump_emdata)
        .def("check_image", &EMAN::TestUtil::check_image, EMAN_TestUtil_check_image_overloads_1_2())
        .def("set_progname", &EMAN::TestUtil::set_progname)
        .def("make_image_file", &EMAN::TestUtil::make_image_file, EMAN_TestUtil_make_image_file_overloads_2_6())
        .def("verify_image_file", &EMAN::TestUtil::verify_image_file, EMAN_TestUtil_verify_image_file_overloads_2_6())
        .def("make_image_file2", &EMAN::TestUtil::make_image_file2, EMAN_TestUtil_make_image_file2_overloads_2_6())
        .def("verify_image_file2", &EMAN::TestUtil::verify_image_file2, EMAN_TestUtil_verify_image_file2_overloads_2_6())
        .staticmethod("test_Vec3f")
        .staticmethod("verify_image_file2")
        .staticmethod("test_vector_float")
        .staticmethod("test_Vec3i")
        .staticmethod("test_map_int")
        .staticmethod("make_image_file")
        .staticmethod("emobject_strarray_to_py")
        .staticmethod("test_map_vecstring")
        .staticmethod("get_debug_int")
        .staticmethod("test_vector_long")
        .staticmethod("emobject_farray_to_py")
        .staticmethod("test_IntPoint")
        .staticmethod("dump_image_from_file")
        .staticmethod("dump_emdata")
        .staticmethod("set_progname")
        .staticmethod("test_map_float")
        .staticmethod("test_IntSize")
        .staticmethod("test_FloatSize")
        .staticmethod("verify_image_file")
        .staticmethod("test_map_long")
        .staticmethod("to_emobject")
        .staticmethod("make_image_file2")
        .staticmethod("emobject_to_py")
        .staticmethod("get_golden_image")
        .staticmethod("test_map_string")
        .staticmethod("test_vector_int")
        .staticmethod("test_vector_emdata")
        .staticmethod("test_vector_string")
        .staticmethod("get_debug_string")
        .staticmethod("test_FloatPoint")
        .staticmethod("test_dict")
        .staticmethod("test_map_emobject")
        .staticmethod("test_vector_pixel")
        .staticmethod("get_debug_float")
        .staticmethod("get_debug_image")
        .staticmethod("check_image")
    ;

    class_< TFList >("TFList", init<  >())
        .def(init< const TFList& >())
        .def(init< int, int >())
        .def(init< int, int, int >())
        .def_readwrite("data", &TFList::data)
        .def_readwrite("nrows", &TFList::nrows)
        .def_readwrite("ncols", &TFList::ncols)
        .def_readwrite("ndigit", &TFList::ndigit)
        .def("read", &TFList::read)
        .def("write", &TFList::write)
        .def("Copy", &TFList::Copy)
        .def("CopyCol", &TFList::CopyCol)
        .def("CopyRow", &TFList::CopyRow)
        .def("SetVal", &TFList::SetVal)
        .def("GetVal", &TFList::GetVal)
    ;

}

