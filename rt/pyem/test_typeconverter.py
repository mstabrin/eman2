#!/bin/env python

from EMAN2 import *
from testlib import *
import os
import sys
import Numeric

import unittest
from test import test_support
import testlib

class TestTypeConverter(unittest.TestCase):


    def test_emobject_to_py(self):
        
        nx = 10
        ny = 12
        nz = 2
        img1 = EMData()
        img1.set_size(nx, ny, nz)        
        img2 = TestUtil.emobject_to_py(img1)
        self.assertEqual(img2.get_xsize(), nx)
        self.assertEqual(img2.get_ysize(), ny)
        self.assertEqual(img2.get_zsize(), nz)

        attr_dict = img2.get_attr_dict()
        self.assertEqual(type(attr_dict["minimum"]), type(2.2))
        self.assertEqual(type(attr_dict["nx"]), type(nx))
        
        n1 = 100
        n2 = TestUtil.emobject_to_py(n1)
        self.assertEqual(n1, n2)

        f1 = 3.14
        f2 = TestUtil.emobject_to_py(f1)
        self.assertEqual(f1, f2)

        str1 = "helloworld"
        str2 = TestUtil.emobject_to_py(str1)
        self.assertEqual(str1, str2)

        farray = TestUtil.emobject_farray_to_py()
        farray2 = testlib.get_list("float")
        self.assertEqual(farray, farray2)

        strarray = TestUtil.emobject_strarray_to_py()
        strarray2 = testlib.get_list("string")
        self.assertEqual(strarray, strarray2)

        testfile = "test_emobject_to_py_xydata.txt"
        out = open(testfile, "wb")
        for f in farray2:
            out.write(str(f) + " " + str(f) + "\n")
        out.close()
        xyd = XYData()
        xyd.read_file(testfile)
        xyd2 = TestUtil.emobject_to_py(xyd)
        self.assertEqual(xyd2.get_size(), len(farray2))
        for i in range(len(farray2)):
            self.assertEqual(xyd2.get_x(i), farray2[i])
            self.assertEqual(xyd2.get_y(i), farray2[i])
        os.unlink(testfile)
        
   
    def test_emobject(self):
        num = TestUtil.get_debug_int(0)
        TestUtil.to_emobject({"int": num})

        fnum = TestUtil.get_debug_float(0)
        TestUtil.to_emobject({"float": fnum})

        lnum = long(num)
        TestUtil.to_emobject({"long": lnum})

        fl = get_list("float")
        TestUtil.to_emobject({"floatarray": fl})

        str1 = TestUtil.get_debug_string(0)
        TestUtil.to_emobject({"string": str1})


        e = EMData()
        nx = TestUtil.get_debug_int(0)
        ny = TestUtil.get_debug_int(1)
        nz = TestUtil.get_debug_int(2)
        e.set_size(nx, ny, nz)
        TestUtil.to_emobject({"emdata": e})

        xyd = XYData()
        testfile = "xydata.txt"
        out = open(testfile, "wb")
        for f in fl:
                out.write(str(f) + " " + str(f) + "\n")
        out.close()

        xyd.read_file(testfile)
        TestUtil.to_emobject({"xydata" : xyd})
        os.unlink(testfile)

        strlist = get_list("string")
        TestUtil.to_emobject({"stringarray":strlist})


    def test_Dict(self):
        edict = get_dict("float")
        edict2 = TestUtil.test_dict(edict)        
        self.assertEqual(edict, edict2)


    def test_point_size(self):
        nlist = get_list("int")
        flist = get_list("float")

        vec3i = TestUtil.test_Vec3i(nlist)
        self.assertEqual(vec3i.as_list(), nlist)

        vec3f = TestUtil.test_Vec3f(flist)
        self.assertEqual(vec3f.as_list(), flist)

        ip1 = TestUtil.test_IntPoint(nlist)
        self.assertEqual(list(ip1), nlist)

        fp1 = TestUtil.test_FloatPoint(flist)
        self.assertEqual(list(fp1), flist)

        is1 = TestUtil.test_IntSize(nlist)
        self.assertEqual(list(is1), nlist)

        fs1 = TestUtil.test_FloatSize(flist)
        self.assertEqual(list(fs1), flist)

    def test_map(self):

        imap = get_dict("int")
        imap2 = TestUtil.test_map_int(imap)
        self.assertEqual(imap, imap2)

        lmap = get_dict("long")
        lmap2 = TestUtil.test_map_long(lmap)
        self.assertEqual(lmap, lmap2)

        fmap = get_dict("float")
        fmap2 = TestUtil.test_map_float(fmap)
        self.assertEqual(fmap, fmap2)

        smap = get_dict("string")
        smap2 = TestUtil.test_map_string(smap)
        self.assertEqual(smap, smap2)

        # emobjectmap = get_dict("emobject")
        # emobjectmap2 = TestUtil.test_map_emobject(emobjectmap)
        # self.assertEqual(emobjectmap, emobjectmap2)


    def test_vector(self):

        nlist = get_list("int")
        flist = get_list("float")
        llist = get_list("long")
        slist = get_list("string")

        nlist2 = TestUtil.test_vector_int(nlist)
        self.assertEqual(nlist, nlist2)

        flist2 = TestUtil.test_vector_float(flist)
        self.assertEqual(flist, flist2)

        llist2 = TestUtil.test_vector_long(llist)
        self.assertEqual(llist, llist2)

        slist2 = TestUtil.test_vector_string(slist)
        self.assertEqual(slist, slist2)


        imgfile1 = "test_vector1.mrc"
        TestUtil.make_image_file(imgfile1, MRC)
        e1 = EMData()
        e1.read_image(imgfile1)
        e2 = EMData()
        e2.set_size(10, 20, 5)
        e3 = EMData()

        elist = [e1, e2, e3]
        elist2 = TestUtil.test_vector_emdata(elist)
        testlib.check_emdata_list(elist, sys.argv[0])
        testlib.check_emdata_list(elist2, sys.argv[0])

        os.unlink(imgfile1)
        
        p1 = Pixel(1,2,3, 1.1)
        p2 = Pixel(4,5,6, 4.4)
        p3 = Pixel(7,8,9, 5.5)

        plist = [p1,p2,p3]
        plist2 = TestUtil.test_vector_pixel(plist)

        self.assertEqual(plist,plist2)


    def test_em2numpy(self):
        imgfile1 = "test_em2numpy_1.mrc"
        nx0 = 100
        ny0 = 200
        TestUtil.make_image_file(imgfile1, MRC, EM_FLOAT, nx0, ny0)
        
        e = EMData()
        e.read_image(imgfile1)
        nx = e.get_xsize()
        ny = e.get_ysize()

        a = EMNumPy.em2numpy(e)
        n = ny/2

        for i in range(nx):
            self.assertEqual(e.get_value_at(i, n), a[n][i])

        self.assertEqual(a.shape, (ny0, nx0))
        self.assertEqual(a.typecode(), "f")

        for x in range(nx):
            for y in range(n):
                a[y][x] = 0

        testlib.check_emdata(e, sys.argv[0])
        
        e2 = EMData()
        EMNumPy.numpy2em(a, e2)
        testlib.check_emdata(e2, sys.argv[0])

        os.unlink(imgfile1)

    def test_numpy2em(self):
        n = 100
        l = range(2*n*n)
        a = Numeric.reshape(Numeric.array(l, Numeric.Float32), (2*n, n))

        self.assertEqual(a.shape, (2*n, n))
        self.assertEqual(a.typecode(), "f")

        e = EMData()
        EMNumPy.numpy2em(a, e)
        testlib.check_emdata(e, sys.argv[0])

        for i in range(n):
            self.assertEqual(e.get_value_at(i, 0), i)


    def test_em2numpy2(self):
        imgfile1 = "test_em2numpy2_1.mrc"
        nx0 = 100
        ny0 = 200
        TestUtil.make_image_file(imgfile1, MRC, EM_FLOAT, nx0, ny0)
        
        e = EMData()
        e.read_image(imgfile1)
        nx = e.get_xsize()
        ny = e.get_ysize()

        a = EMNumPy.em2numpy(e)
        print a[-1, 0:4]
        print a
        print a[-1, 0:4]


    def test_Point_and_Size_class(self):
        imgfile1 = "test_Point_and_Size_class_1.mrc"
        TestUtil.make_image_file(imgfile1, MRC, EM_FLOAT, 32,32,32)

        img1 = EMData()
        img1.read_image(imgfile1)

        ptuple1 = (16,16,16)
        plist1 = list(ptuple1)
        
        img2=img1.get_rotated_clip(Transform(plist1, EULER_EMAN, 0,0,0), plist1, 1.0)
        img3=img1.get_rotated_clip(Transform(ptuple1, EULER_EMAN, 0,0,0), ptuple1, 1.0)
        
        testlib.check_emdata(img2, sys.argv[0])
        testlib.check_emdata(img3, sys.argv[0])

        os.unlink(imgfile1)


def test_main():
    test_support.run_unittest(TestTypeConverter)

if __name__ == '__main__':
    test_main()




