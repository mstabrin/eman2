#!/usr/bin/env python


# Author: David Woolford, 12/9/2008 (woolford@bcm.edu)
# Copyright (c) 2000-2007 Baylor College of Medicine
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
#



from EMAN2 import *
from optparse import OptionParser
from math import *
import os
import sys
import pyemtbx.options

from e2refine import check_make3d_args,get_classaverage_cmd,check_classaverage_args,get_make3d_cmd

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options] 
	EMAN2 even odd test
	
	Typically usage is e2eotest.py [similar options that were passed to e2refine] --path=refine_02
	
	Output is written to the EMAN2 database corresponding to the path argument, specifically it is inserted the fsc.results entry.
	
	"""
	parser = OptionParser(usage=usage,version=EMANVERSION)
	
	parser.add_option("--path", default=None, type="string",help="The name the e2refine directory that contains the reconstruction data.")
	parser.add_option("--iteration",default=None,type="string",help="Advanced. Can be used to perform the eotest using data from specific rounds of iterative refinement. In unspecified that most recently generated class data are used.")
	parser.add_option("--usefilt", dest="usefilt", default=None, help="Specify a particle data file that has been low pass or Wiener filtered. Has a one to one correspondence with your particle data. If specified will be used in projection matching routines, and elsewhere.")
	parser.add_option("--sym", dest = "sym", help = "Specify symmetry - choices are: c<n>, d<n>, h<n>, tet, oct, icos",default=None)
	parser.add_option("--verbose","-v", dest="verbose", default=False, action="store_true",help="Toggle verbose mode - prints extra infromation to the command line while executing")
	parser.add_option("--lowmem", default=False, action="store_true",help="Make limited use of memory when possible - useful on lower end machines")
	parser.add_option("--force","-f", default=False, action="store_true",help="Force overwrite previously existing files")
	
	
	# options associated with e2classaverage.py
	parser.add_option("--classkeep",type="float",help="The fraction of particles to keep in each class, based on the similarity score generated by the --cmp argument.")
	parser.add_option("--classkeepsig", default=False, action="store_true", help="Change the keep (\'--keep\') criterion from fraction-based to sigma-based.")
	parser.add_option("--classiter", type="int", help="The number of iterations to perform. Default is 1.", default=3)
	parser.add_option("--classalign",type="string",help="If doing more than one iteration, this is the name and parameters of the 'aligner' used to align particles to the previous class average.", default="rotate_translate")
	parser.add_option("--classaligncmp",type="string",help="This is the name and parameters of the comparitor used by the fist stage aligner  Default is dot.",default="phase")
	parser.add_option("--classralign",type="string",help="The second stage aligner which refines the results of the first alignment in class averaging. Default is None.", default=None)
	parser.add_option("--classraligncmp",type="string",help="The comparitor used by the second stage aligner in class averageing. Default is dot:normalize=1.",default="dot:normalize=1")
	parser.add_option("--classaverager",type="string",help="The averager used to generate the class averages. Default is \'image\'.",default="image")
	parser.add_option("--classcmp",type="string",help="The name and parameters of the comparitor used to generate similarity scores, when class averaging. Default is \'dot:normalize=1\'", default="dot:normalize=1")
	parser.add_option("--classnormproc",type="string",default="normalize.edgemean",help="Normalization applied during class averaging")
	
	
	#options associated with e2make3d.py
	parser.add_option("--pad", type=int, dest="pad", help="To reduce Fourier artifacts, the model is typically padded by ~25% - only applies to Fourier reconstruction", default=0)
	parser.add_option("--recon", dest="recon", default="fourier", help="Reconstructor to use see e2help.py reconstructors -v")
	parser.add_option("--m3dkeep", type=float, help="The percentage of slices to keep in e2make3d.py")
	parser.add_option("--m3dkeepsig", default=False, action="store_true", help="The standard deviation alternative to the --m3dkeep argument")
	parser.add_option("--m3diter", type=int, default=4, help="The number of times the 3D reconstruction should be iterated")
	parser.add_option("--m3dpreprocess", type="string", default="normalize.edgemean", help="Normalization processor applied before 3D reconstruction")
	
	(options, args) = parser.parse_args()
	
	error = False
	if check(options) == True :
		# in eotest the first check fills in a lot of the blanks in the options, so if it fails just exit - it printed error messages for us
		exit(1)
	
	if check_output_files(options) == True:
		error = True
	if check_classaverage_args(options,True) == True :
		error = True
	if check_make3d_args(options,True) == True:
		error = True
		
	if options.force:
		remove_output_files(options)
	
	logid=E2init(sys.argv)
	
	if error:
		print "Error encountered while checking command line, bailing"
		
		exit_eotest(1,logid)
		
	else:
		progress = 0.0
		total_procs = 4.0
		for tag in ["even","odd"]:
			options.cafile = "bdb:"+options.path+"#classes_"+options.iteration+"_" + tag
			options.model = "bdb:"+options.path+"#threed_"+options.iteration+"_" + tag
			options.resultfile = "bdb:"+options.path+"#cls_result_"+options.iteration+"_" + tag
			
			cmd = get_classaverage_cmd(options)
			cmd += " --%s" %tag
			if ( os.system(cmd) != 0 ):
				print "Failed to execute %s" %get_classaverage_cmd(options)
				exit_eotest(1,logid)
			progress += 1.0
			E2progress(logid,progress/total_procs)
				
			if ( os.system(get_make3d_cmd(options)) != 0 ):
				print "Failed to execute %s" %get_make3d_cmd(options)
				exit_eotest(1,logid)
			progress += 1.0
			E2progress(logid,progress/total_procs)
			
		
		a = EMData("bdb:"+options.path+"#threed_"+options.iteration+"_even",0)
		b = EMData("bdb:"+options.path+"#threed_"+options.iteration+"_odd",0)
		
		fsc = a.calc_fourier_shell_correlation(b)
		third = len(fsc)/3
		xaxis = fsc[0:third]
		plot = fsc[third:2*third]
		error = fsc[2*third:]
		
		db = db_open_dict("bdb:"+options.path+"#convergence.results")
		db["even_odd_"+options.iteration+"_fsc"] = [xaxis,plot]
		db["error_even_odd_"+options.iteration+"_fsc"] = [xaxis,error]
		db_close_dict("bdb:"+options.path+"#convergence.results")
		
		
					
		exit_eotest(0,logid)
			
def exit_eotest(n,logid):
	E2end(logid)
	exit(n)

def check_output_files(options):
	error = False
	if not options.force:
		for tag in ["even","odd"]:
			cafile = "bdb:"+options.path+"#classes_"+options.iteration+"_" + tag
			model = "bdb:"+options.path+"#threed_"+options.iteration+"_" + tag
			resultfile = "bdb:"+options.path+"#cls_result_"+options.iteration+"_" + tag
			op = [cafile,model,resultfile]
			for o in op:
				if file_exists(o):
					print "Error, %s file exists, specify the force argument to automatically overwrite it" %o
 					error = True	
	
	return error

def remove_output_files(options):
	
	if not options.force:
		for tag in ["even","odd"]:
			cafile = "bdb:"+options.path+"#classes_"+options.iteration+"_" + tag
			model = "bdb:"+options.path+"#threed_"+options.iteration+"_" + tag
			resultfile = "bdb:"+options.path+"#cls_result_"+options.iteration+"_" + tag
			op = [cafile,model,resultfile]
			for o in op:
				if file_exists(o):
					remove_file(o)
	

def check(options):
	error = False
	
	if options.path == None or not os.path.exists(options.path):
			print "Error: the path %s does not exist" %options.path
			error = True
			
	else:
		if options.iteration != None and options.path != None:
			nec_files = [ "classes_", "classify_"]
			dir = options.path
			for file in nec_files:
				db_name = "bdb:"+dir+"#" + file + options.iteration
				if not db_check_dict(db_name):
					print "Error: %s doesn't exist", db_name
					error= True
					
		if not get_last_class_average_number(options):
			print "Error: you have specified an invalid path - refinement data is incomplete in %s", options.path
			error = True
	
	if options.sym == None or len(options.sym) == 0:
		print "Error: you must specify the sym argument"
		error = True
	else:
		if options.sym not in ["icos","tet","oct"]:
			if options.sym[0] in ["c","d","h"]:
				try:
					int(options.sym[1:])
				except:
					print "Error:unknown symmetry argument %s" %options.sym
					error = True
			else:
				print "Error:unknown symmetry argument %s" %options.sym
				error = True
				
	return error

	

def get_last_class_average_number(options):
		'''
		Looks for bdb:refine_??#classes_?? files - should also be a corresponding  classify_?? file, and "all" should exist which should have as many particles as there are
		entries in the classification file. Returns a string such as "00" or "01" if successful. If failure returns None
		'''
		
		nec_files = [ "classes_", "classify_","projections_"]
		
		dir = options.path
		most_recent = options.iteration
		if most_recent == None:
			for i in range(0,9):
				for j in range(0,9):
					end = str(i) + str(j)
					fail = False
					for file in nec_files:
						db_first_part = "bdb:"+dir+"#" + file
						db_name = db_first_part + end
						if not db_check_dict(db_name):
							fail = True
							break
					if not fail:
						most_recent = end
					
		if most_recent != None:
			nx,ny = gimme_image_dimensions2D("bdb:"+dir+"#classify_"+most_recent)
			np = EMUtil.get_image_count("bdb:"+dir+"#all")
			if ny != np:
				print "Error, the number of particles in the 'all' image does not match the number of rows in the classification image"
				return None
			else:
				options.iteration = most_recent
				options.input = "bdb:"+dir+"#all"
				options.classifyfile = "bdb:"+dir+"#classify_"+most_recent
				options.projfile = "bdb:"+dir+"#projections_"+most_recent
				options.cafile = "bdb:"+dir+"#classes_"+most_recent+"_even"
				options.model = "bdb:"+dir+"#threed_"+most_recent+"_even"
			
		if most_recent == None:
			print "Error, there is no valid classification data in %s",dir
			# return statement below takes care of returning None
						
		return most_recent	
					
	
#	
#def get_make3d_cmd(options,check=False,nofilecheck=False):
#	e2make3dcmd = "e2make3d.py %s --sym=%s --iter=%d -f" %(options.cafile,options.sym,options.m3diter)
#	
#	e2make3dcmd += " --recon=%s --out=%s" %(options.recon,options.model)
#
#	if str(options.m3dpreprocess) != "None":
#		e2make3dcmd += " --preprocess=%s" %options.m3dpreprocess
#
#	
#	if (options.m3dkeep):
#		e2make3dcmd += " --keep=%f" %options.m3dkeep
#		if (options.m3dkeepsig): e2make3dcmd += " --keepsig"
#	
#	if (options.lowmem): e2make3dcmd += " --lowmem"
#
#	if (options.pad != 0):
#		e2make3dcmd += " --pad=%d" %options.pad
#		
#	if (options.verbose):
#		e2make3dcmd += " -v"
#	
#	if ( check ):
#		e2make3dcmd += " --check"	
#			
#	if ( nofilecheck ):
#		e2make3dcmd += " --nofilecheck"
#	
#	return e2make3dcmd
#
#def check_make3d_args(options, nofilecheck=False):
#	
#	cmd = get_make3d_cmd(options,True,nofilecheck)
#	print ""
#	print "#### Test executing make3d command: %s" %cmd
#	return ( os.system(cmd) != 0)
#
#def get_classaverage_cmd(options,check=False,nofilecheck=False):
#	
#	e2cacmd = "e2classaverage.py %s %s %s" %(options.input,options.classifyfile,options.cafile)
#	
#	e2cacmd += " --ref=%s --iter=%d -f --result=%s --normproc=%s" %(options.projfile,options.classiter,options.resultfile,options.classnormproc)
#	
#	e2cacmd += " --idxcache --dbpath=%s" %options.path
#	
#	if (options.classkeep):
#		e2cacmd += " --keep=%f" %options.classkeep
#		
#	if (options.classkeepsig):
#		e2cacmd += " --keepsig"
#	
#	if (options.classiter >= 1 ):
#		e2cacmd += " --cmp=%s --align=%s --aligncmp=%s" %(options.classcmp,options.classalign,options.classaligncmp)
#
#		if (options.classralign != None):
#			e2cacmd += " --ralign=%s --raligncmp=%s" %(options.classralign,options.classraligncmp)
#	
#	if options.usefilt != None:
#		e2cacmd += " --usefilt=%s" %options.usefilt
#	
#	if (options.verbose):
#		e2cacmd += " -v"
#		
#	if (options.lowmem): e2cacmd += " --lowmem"
#	
#	if ( check ):
#		e2cacmd += " --check"	
#			
#	if ( nofilecheck ):
#		e2cacmd += " --nofilecheck"
#	
#	return e2cacmd

if __name__ == "__main__":
    main()