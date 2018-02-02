#!/usr/bin/env python
from __future__ import print_function

#
# Author: James Michael Bell, 03/27/2017 (jmbell@bcm.edu)
# Copyright (c) 2000-2013 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#

from EMAN2 import *
import numpy as np
import sys
import os

def main():

	progname = os.path.basename(sys.argv[0])
	usage = """prog [options] <ddd_movie_stack>

	This program will do various processing operations on "movies" recorded on direct detection cameras. It
	is primarily used to do whole-frame alignment of movies using all-vs-all CCFs with a global optimization
	strategy. Several outputs including different frame subsets are produced, as well as a text file with the
	translation vector map.

	Note: We have found the following to work on DE64 images:
	e2ddd_movie.py <movies> --de64 --dark <dark_frames> --gain <gain_frames> --gain_darkcorrected --reverse_gain --invert_gain

	Note: For multi-image files in MRC format, use the .mrcs extension. Do not use .mrc, as it will handle input stack as a 3D volume.
	"""

	parser = EMArgumentParser(usage=usage,version=EMANVERSION)

	parser.add_argument('--darkrefs', nargs='+',help="List the dark references to import and process.", default=[], guitype='filebox', browser="EMMovieDataTable(withmodal=True,multiselect=True)",  row=0, col=0,rowspan=1, colspan=3, mode="default")
	#parser.add_argument(name="--darkrefs",type=str,default="",help="Perform dark image correction using the specified image file",guitype='filebox',browser="EMMovieDataTable(withmodal=True,multiselect=True)", row=4, col=0, rowspan=1, colspan=3, mode="align,tomo")
	parser.add_argument("--rotate_dark",  default = "0", type=str, choices=["0","90","180","270"], help="Rotate dark reference by 0, 90, 180, or 270 degrees. Default is 0. Transformation order is rotate then reverse.",guitype='combobox', choicelist='["0","90","180","270"]', row=5, col=0, rowspan=1, colspan=1, mode="default")
	parser.add_argument("--reverse_dark", default=False, help="Flip dark reference along y axis. Default is False. Transformation order is rotate then reverse.",action="store_true",guitype='boolbox', row=5, col=1, rowspan=1, colspan=1, mode="default")

	parser.add_argument('--gainrefs', nargs='+',help="List the gain references to import and process.", default=[], guitype='filebox', browser="EMMovieDataTable(withmodal=True,multiselect=True)",  row=0, col=0,rowspan=1, colspan=3, mode="default")
	#parser.add_argument("--gainrefs",type=str,default="",help="Perform gain image correction using the specified image file",guitype='filebox',browser="EMMovieDataTable(withmodal=True,multiselect=True)", row=6, col=0, rowspan=1, colspan=3, mode="align,tomo")
	parser.add_argument("--rotate_gain", default = 0, type=str, choices=["0","90","180","270"], help="Rotate gain reference by 0, 90, 180, or 270 degrees. Default is 0. Transformation order is rotate then reverse.",guitype='combobox', choicelist='["0","90","180","270"]', row=7, col=1, rowspan=1, colspan=1, mode="default")
	parser.add_argument("--reverse_gain", default=False, help="Flip gain reference along y axis (about x axis). Default is False. Transformation order is rotate then reverse.",action="store_true",guitype='boolbox', row=7, col=2, rowspan=1, colspan=1, mode="default")
	#parser.add_argument("--gain_darkcorrected", default=False, help="Do not dark correct gain image. False by default.",action="store_true",guitype='boolbox', row=8, col=1, rowspan=1, colspan=1, mode="default")
	parser.add_argument("--invert_gain", default=False, help="Use reciprocal of input gain image",action="store_true",guitype='boolbox', row=8, col=2, rowspan=1, colspan=1, mode="default")

	parser.add_argument("--k2", default=False, help="Perform gain image correction on gain images from a Gatan K2. Note, these are the reciprocal of typical DDD gain images.",action="store_true",guitype='boolbox', row=7, col=0, rowspan=1, colspan=1, mode="align,tomo")
	parser.add_argument("--de64", default=False, help="Perform gain image correction on DE64 data. Note, these should not be normalized.",action="store_true",guitype='boolbox', row=8, col=0, rowspan=1, colspan=1, mode="align,tomo")

	parser.add_argument("--fixbadpixels",action="store_true",default=False,help="Tries to identify bad pixels in the dark/gain reference, and fills images in with sane values instead", guitype='boolbox', row=17, col=1, rowspan=1, colspan=1, mode='align[True],tomo[True]')

	parser.add_header(name="orblock4", help='Just a visual separation', title="Output: ", row=10, col=0, rowspan=2, colspan=1, mode="align,tomo")
	
	parser.add_argument("--verbose", "-v", dest="verbose", action="store", metavar="n", type=int, default=0, help="verbose level [0-9], higner number means higher level of verboseness")
	#parser.add_argument("--debug", default=False, action="store_true", help="run with debugging output")
	parser.add_argument("--ppid", type=int, help="Set the PID of the parent process, used for cross platform PPID",default=-2)

	(options, args) = parser.parse_args()

	pid=E2init(sys.argv)

	moviesdir = os.path.join(".","movierefs")
	if not os.access(moviesdir, os.R_OK):
		os.mkdir(moviesdir)

	if len(options.darkrefs) > 0:
		print("Importing Dark References")
		for df in options.darkrefs:
			if df[-4:].lower() in (".mrc") :
				dark_hdr = EMData(df,0,True)
				nx = dark_hdr["nx"]
				ny = dark_hdr["ny"]
				nd = dark_hdr["nz"]
				dark=EMData(df,0,False,Region(0,0,0,nx,ny,1))
			else:
				nd=EMUtil.get_image_count(df)
				dark = EMData(df,0)
				nx = dark["nx"]
				ny = dark["ny"]
			if nd>1:
				sigd=dark.copy()
				sigd.to_zero()
				a=Averagers.get("mean",{"sigma":sigd,"ignore0":1})
				print("Averaging Dark Frames")
				for i in xrange(0,nd):
					if options.verbose:
						sys.stdout.write("({}/{})   \r".format(i+1,nd))
						sys.stdout.flush()
					if options.dark[-4:].lower() in (".mrc"):
						t=EMData(df,0,False,Region(0,0,i,nx,ny,1))
					else: 
						t=EMData(df,i)
					t.process_inplace("threshold.clampminmax",{"minval":0,"maxval":t["mean"]+t["sigma"]*3.5,"tozero":1})
					a.add_image(t)
				dark=a.finish()
			
			sigd.process_inplace("threshold.binary",{"value":sigd["sigma"]/10.0}) # Theoretically a "perfect" pixel would have zero sigma, but in reality, the opposite is true
			dark.mult(sigd)

			dfout = "{}/{}".format(moviesdir,base_name(df))
			bn,ext = dfout.split(".")
			dark.write_image(dfout)
			sigd.write_image("{}_sig.{}".format(bn,ext))

	if len(options.gainrefs)>0::
		print("Loading Gain References")
		for gf in options.gainrefs:
			if options.k2: gain=EMData(gf)
			else:
				if gf[-4:].lower() in (".mrc") :
					gain_hdr = EMData(gf,0,True)
					nx = gain_hdr["nx"]
					ny = gain_hdr["ny"]
					nd = gain_hdr["nz"]
					gain=EMData(gf,0,False,Region(0,0,0,nx,ny,1))
				else:
					nd=EMUtil.get_image_count(gf)
					gain = EMData(gf,0)
					nx = gain["nx"]
					ny = gain["ny"]
				if nd>1:
					sigg=gain.copy()
					sigg.to_zero()
					a=Averagers.get("mean",{"sigma":sigg,"ignore0":1})
					print("Averaging Gain Frames")
					for i in xrange(0,nd):
						if options.verbose:
							sys.stdout.write("({}/{})   \r".format(i+1,nd))
							sys.stdout.flush()
						if gf[-4:].lower() in (".mrc") :
							t=EMData(gf,0,False,Region(0,0,i,nx,ny,1))
						else:
							t=EMData(gf,i)
						t.process_inplace("threshold.clampminmax",{"minval":0,"maxval":t["mean"]+t["sigma"]*3.5,"tozero":1})
						a.add_image(t)
					gain=a.finish()

			if options.de64:
				gain.process_inplace( "threshold.clampminmax", { "minval" : gain[ 'mean' ] - 8.0 * gain[ 'sigma' ], "maxval" : gain[ 'mean' ] + 8.0 * gain[ 'sigma' ], "tomean" : True } )
			else: 
				gain.process_inplace("math.reciprocal",{"zero_to":0.0})

			sigg.write_image(gf.rsplit(".",1)[0]+"_sig.hdf")
			sigg.process_inplace("threshold.binary",{"value":sigg["sigma"]/10.0}) # Theoretically a "perfect" pixel would have zero sigma, but in reality, the opposite is true
			gain.mult(sigg)

			if options.de64: 
				gain.process_inplace( "threshold.clampminmax", { "minval" : gain['mean']-8.0*gain['sigma'], "maxval":gain['mean']+8.0*gain['sigma'], "tomean":True} )
			else: 
				gain.process_inplace("math.reciprocal",{"zero_to":0.0})

			gain.mult(1.0/gain["mean"])

			dfout = "{}/{}".format(moviesdir,base_name(df))
			bn,ext = dfout.split(".")
			dark.write_image(dfout)
			sigd.write_image("{}_sig.{}".format(bn,ext))				

	E2end(pid)

if __name__ == "__main__":
	main()
