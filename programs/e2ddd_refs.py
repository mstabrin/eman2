#!/usr/bin/env python

def main():

    progname = os.path.basename(sys.argv[0])
    usage = """prog [options] <ddd_movie_stack>

	This program will do various processing operations on "movies" recorded on direct detection cameras. It
	is primarily used to do whole-frame alignment of movies using all-vs-all CCFs with a global optimization
	strategy. Several outputs including different frame subsets are produced, as well as a text file with the
	translation vector map.

	See e2ddd_particles for per-particle alignment.

	Note: We have found the following to work on DE64 images:
	e2ddd_movie.py <movies> --de64 --dark <dark_frames> --gain <gain_frames> --gain_darkcorrected --reverse_gain --invert_gain

	Note: For multi-image files in MRC format, use the .mrcs extension. Do not use .mrc, as it will handle input stack as a 3D volume.
	"""

    parser = EMArgumentParser(usage=usage,version=EMANVERSION)

    # parser.add_pos_argument(name="movies",help="List the movies to align.", default="", guitype='filebox', browser="EMMovieDataTable(withmodal=True,multiselect=True)",  row=0, col=0,rowspan=1, colspan=3, mode="import")

    parser.add_header(name="orblock1", help='Just a visual separation', title="Dark/Gain Correction", row=2, col=0, rowspan=1, colspan=1, mode="import")

    parser.add_argument("--label",type=str,default="",help="Optional: Specify a label for the averaged dark and gain references when using multiple, individual frames.\nA labeled will be written as movierefs/dark_<label>.hdf and movierefs/gain_<label>.hdf.\nNote: This option is ignored when using a single reference image/stack.",guitype='strbox', row=2, col=1, rowspan=1, colspan=2, mode="import")

    parser.add_argument("--dark_frames",type=str,default="",help="Perform dark image correction using the specified image file",guitype='filebox',browser="EMMovieRefsTable(withmodal=True,multiselect=True)", row=4, col=0, rowspan=1, colspan=3, mode="import")

    parser.add_argument("--rotate_dark",  default = "0", type=str, choices=["0","90","180","270"], help="Rotate dark reference by 0, 90, 180, or 270 degrees. Default is 0. Transformation order is rotate then reverse.",guitype='combobox', choicelist='["0","90","180","270"]', row=5, col=0, rowspan=1, colspan=1, mode="import")
    parser.add_argument("--reverse_dark", default=False, help="Flip dark reference along y axis. Default is False. Transformation order is rotate then reverse.",action="store_true",guitype='boolbox', row=5, col=1, rowspan=1, colspan=1, mode="import")

    parser.add_argument("--gain_frames",type=str,default="",help="Perform gain image correction using the specified image file",guitype='filebox',browser="EMMovieRefsTable(withmodal=True,multiselect=True)", row=6, col=0, rowspan=1, colspan=3, mode="import")
    parser.add_argument("--k2", default=False, help="Perform gain image correction on gain images from a Gatan K2. Note, these are the reciprocal of typical DDD gain images.",action="store_true",guitype='boolbox', row=8, col=0, rowspan=1, colspan=1, mode="import")
    parser.add_argument("--rotate_gain", default = 0, type=str, choices=["0","90","180","270"], help="Rotate gain reference by 0, 90, 180, or 270 degrees. Default is 0. Transformation order is rotate then reverse.",guitype='combobox', choicelist='["0","90","180","270"]', row=8, col=1, rowspan=1, colspan=1, mode="import")
    parser.add_argument("--reverse_gain", default=False, help="Flip gain reference along y axis (about x axis). Default is False. Transformation order is rotate then reverse.",action="store_true",guitype='boolbox', row=8, col=2, rowspan=1, colspan=1, mode="import")
    parser.add_argument("--de64", default=False, help="Perform gain image correction on DE64 data. Note, these should not be normalized.",action="store_true",guitype='boolbox', row=9, col=0, rowspan=1, colspan=1, mode="import")
    parser.add_argument("--gain_darkcorrected", default=False, help="Do not dark correct gain image. False by default.",action="store_true",guitype='boolbox', row=9, col=1, rowspan=1, colspan=1, mode="import")
    parser.add_argument("--invert_gain", default=False, help="Use reciprocal of input gain image",action="store_true",guitype='boolbox', row=9, col=2, rowspan=1, colspan=1, mode="import")

    # program designed to take gain references in all possible forms and generate corrected reference images
    # note, with this approach, we deprecate the bad pixel identification strategy that utilizes the gain/dark sigma images.
    # instead, we opt to locate such bad pixels in the final, averaged image for flexibility when handling single frame gain/dark refs

    if options.dark != "" or options.gain != "":
        refsdir = os.path.join(".","movierefs")
        if not os.access(refsdir, os.R_OK):
            os.mkdir(refsdir)

    dark_source = options.dark
    gain_source = options.gain

    dark_lst = ""
    gain_lst = ""

    if len(options.dark.split(",")) > 1:
        if options.label:

        else:
            count = 0
            for f in os.listdir("movierefs"):
                if "dark{}.hdf".format(count) in f: count += 1
            newfile = "movierefs/dark_{}.lst".format(count)
        run("e2proclst.py {} --create {}".format(options.dark.replace(","," "),newfile))
        options.dark = newfile
        dark_lst = newfile

    if len(options.gain.split(",")) > 1:
        count = 0
        for f in os.listdir("movierefs"):
            if "gain{}.hdf".format(count) in f:
                count += 1
        newfile = "movierefs/gain_{}.lst".format(count)
        run("e2proclst.py {} --create {}".format(options.gain.replace(","," "),newfile))
        options.gain = newfile
        gain_lst = newfile

    dark,gain = process_refs(options)

    if dark != None:

        darkref = "movierefs/{}.hdf".format(base_name(options.dark,nodir=True))
        dark.write_image(darkref,0)

        db=js_open_dict(info_name(darkref,nodir=True))
        db["data_source"]=fsp
        if dark_lst != "": db["data_lst"]=dark_lst
        db["ddd_dark_reference"] = darkref
        if options.rotate_dark: db["ddd_rotate_dark"]=options.rotate_dark
        if options.reverse_dark: db["ddd_reverse_dark"]=options.reverse_dark
        if options.bad_rows: db["ddd_bad_rows"] = options.bad_rows
        if options.bad_columns: db["ddd_bad_columns"] = options.bad_columns
        db.close()

    if gain != None:

        options.gain = "movierefs/{}.hdf".format(base_name(options.gain,nodir=True))
        gain.write_image(options.gain,0)

        db=js_open_dict(info_name(options.gain,nodir=True))
        db["data_source"]=gain_source
        if gain_lst != "": db["data_lst"]=gain_lst
        db["ddd_gain_reference"] = options.gain
        if options.rotate_gain: db["ddd_rotate_gain"] = options.rotate_gain
        if options.reverse_gain: db["ddd_reverse_gain"] = options.reverse_gain
        if options.invert_gain: db["ddd_invert_gain"] = options.invert_gain
        if options.gain_darkcorrected: db["ddd_gain_darkcorrected"] = options.gain_darkcorrected
        if options.bad_rows: db["ddd_bad_rows"] = options.bad_rows
        if options.bad_columns: db["ddd_bad_columns"] = options.bad_columns
        db.close()

    return

def process_refs(options):
    if options.dark != "":
        print("Loading Dark Reference")
        if options.dark[-4:].lower() in (".mrc") :
            dark_hdr = EMData(options.dark,0,True)
            nx = dark_hdr["nx"]
            ny = dark_hdr["ny"]
            nd = dark_hdr["nz"]
            dark=EMData(options.dark,0,False,Region(0,0,0,nx,ny,1))
        else:
            nd=EMUtil.get_image_count(options.dark)
            dark = EMData(options.dark,0)
            nx = dark["nx"]
            ny = dark["ny"]
        if nd>1:
            sigd=dark.copy()
            sigd.to_zero()
            a=Averagers.get("mean",{"sigma":sigd,"ignore0":1})
            print("Summing Dark Frames")
            for i in xrange(0,nd):
                if options.verbose:
                    sys.stdout.write("({}/{})   \r".format(i+1,nd))
                    sys.stdout.flush()
                if options.dark[-4:].lower() in (".mrc") :
                    t=EMData(options.dark,0,False,Region(0,0,i,nx,ny,1))
                else:
                    t=EMData(options.dark,i)
                t.process_inplace("threshold.clampminmax",{"minval":0,"maxval":t["mean"]+t["sigma"]*3.5,"tozero":1})
                a.add_image(t)
            dark=a.finish()
        dark.process_inplace("threshold.clampminmax.nsigma",{"nsigma":3.0})

        if options.rotate_dark and dark != None:
            tf = Transform({"type":"2d","alpha":int(options.rotate_dark)})
            dark.process_inplace("xform",{"transform":tf})

        if options.reverse_dark: dark.process_inplace("xform.reverse",{"axis":"y"})

        options.dark = "movierefs/{}.hdf".format(base_name(options.dark,nodir=True))
        dark.write_image(options.dark,0)

    else : dark=None

    if options.gain != "":
        print("Loading Gain Reference")
        if options.k2: gain=EMData(options.gain)
        else:
            if options.gain[-4:].lower() in (".mrc") :
                gain_hdr = EMData(options.gain,0,True)
                nx = gain_hdr["nx"]
                ny = gain_hdr["ny"]
                nd = gain_hdr["nz"]
                gain=EMData(options.gain,0,False,Region(0,0,0,nx,ny,1))
            else:

                nd=EMUtil.get_image_count(options.gain)
                gain = EMData(options.gain,0)
                nx = gain["nx"]
                ny = gain["ny"]
            if nd>1:
                sigg=gain.copy()
                sigg.to_zero()
                a=Averagers.get("mean",{"sigma":sigg,"ignore0":1})
                print("Summing Gain Frames")
                for i in xrange(0,nd):
                    if options.verbose:
                        sys.stdout.write("({}/{})   \r".format(i+1,nd))
                        sys.stdout.flush()
                    if options.dark != "" and options.dark[-4:].lower() in (".mrc") :
                        t=EMData(options.gain,0,False,Region(0,0,i,nx,ny,1))
                    else:
                        t=EMData(options.gain,i)
                    t.process_inplace("threshold.clampminmax",{"minval":0,"maxval":t["mean"]+t["sigma"]*3.5,"tozero":1})
                    a.add_image(t)
                gain=a.finish()
            if options.de64:
                gain.process_inplace( "threshold.clampminmax", { "minval" : gain[ 'mean' ] - 8.0 * gain[ 'sigma' ], "maxval" : gain[ 'mean' ] + 8.0 * gain[ 'sigma' ], "tomean" : True } )
            else:
                gain.process_inplace("math.reciprocal",{"zero_to":0.0})

        if dark!="" and options.gain != "" and options.gain_darkcorrected == False: gain.sub(dark) # dark correct the gain-reference

        if options.de64:
            mean_val = gain["mean"]
            if mean_val <= 0.: mean_val=1.
            gain.process_inplace("threshold.belowtominval",{"minval":0.01,"newval":mean_val})

        gain.mult(1.0/gain["mean"])

        if options.invert_gain: gain.process_inplace("math.reciprocal")

        if options.rotate_gain and gain != None:
            tf = Transform({"type":"2d","alpha":int(options.rotate_gain)})
            gain.process_inplace("xform",{"transform":tf})

        if options.reverse_gain: gain.process_inplace("xform.reverse",{"axis":"y"})

    else: gain=None

    return dark,gain


if __name__ == "__main__":
    main()