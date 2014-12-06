#!/usr/bin/env python

#
# Author: Steven Ludtke, 04/11/14 (sludtke@bcm.edu)
# Copyright (c) 2000- Baylor College of Medicine
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

import pprint
from EMAN2 import *
import sys
import os
from numpy import *
import numpy.linalg as LA
import threading

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """prog [options] <refine_xx folder>

	WARNING: this program is still considered experimental!

	Based on a completed refinement, this will perform per-particle alignment using reference projections from the reconstruction.
	It will only perform alignments on particles used in the specified refinement run. 
	
	This will make an attempt to rename the original particles as *__orig before writing the new particles with the original particle
	names. It will do this only the first time. If __orig files already exist, it will not replace them. This way if you run this
	program multiple times, you can produce new versions of the aligned particles without destroying the true originals.
	"""
	
	parser = EMArgumentParser(usage=usage,version=EMANVERSION)
	
	#parser.add_argument("--align_frames", action="store_true",help="Perform whole-frame alignment of the stack",default=False)
	#parser.add_argument("--save_aligned", action="store_true",help="Save aligned stack",default=False)
	#parser.add_argument("--dark",type=str,default=None,help="Perform dark image correction using the specified image file")
	#parser.add_argument("--gain",type=str,default=None,help="Perform gain image correction using the specified image file")
	#parser.add_argument("--gaink2",type=str,default=None,help="Perform gain image correction. Gatan K2 gain images are the reciprocal of DDD gain images.")
	#parser.add_argument("--step",type=str,default="1,1",help="Specify <first>,<step>,[last]. Processes only a subset of the input data. ie- 0,2 would process all even particles. Same step used for all input files. [last] is exclusive. Default= 1,1 (first image skipped)")
	#parser.add_argument("--frames",action="store_true",default=False,help="Save the dark/gain corrected frames")
	#parser.add_argument("--normalize",action="store_true",default=False,help="Apply edgenormalization to input images after dark/gain")
	#parser.add_argument("--movie", type=int,help="Display an n-frame averaged 'movie' of the stack, specify number of frames to average",default=0)
	#parser.add_argument("--simpleavg", action="store_true",help="Will save a simple average of the dark/gain corrected frames (no alignment or weighting)",default=False)
	#parser.add_argument("--avgs", action="store_true",help="Testing",default=False)
	parser.add_argument("--noalign",action="store_true",help="Regenerates unaligned particle averages into __orig",default=False)
	parser.add_argument("--invert",action="store_true",help="Invert the contrast of the particles in output files (default false)",default=False)
	parser.add_argument("--filefilt",type=str,help="Only processes image stacks where the filename contains the specified string. Mostly used for debugging.",default=None)
	parser.add_argument("--frac",type=str,help="Processes a fraction of the data, used automatically by --threads. <n>,<ntot>",default=None)
	parser.add_argument("--step",type=str,default="0,-1,1",help="Specify <first>,<last>,<step>. Processes only a subset of the input data. For example, 0,6,2 would process only particles 0,2,4. first is inclusive, last exclusive")
	parser.add_argument("--parallel", default=None, help="parallelism argument. This program supports only thread:<n>")
	parser.add_argument("--threads", default=1,type=int,help="Number of threads to run in parallel on a single computer when multi-computer parallelism isn't useful")
	parser.add_argument("--ppid", type=int, help="Set the PID of the parent process, used for cross platform PPID",default=-2)
	parser.add_argument("--verbose", "-v", dest="verbose", action="store", metavar="n", type=int, default=0, help="verbose level [0-9], higner number means higher level of verboseness")
	
	(options, args) = parser.parse_args()
	
	if len(args)!=1:
		print usage
		parser.error("Specify refine_xx folder")

	# If called with parallelism, the program calls itself with frac. If both were specified, bad things would happen
	if options.frac!=None:
		try: 
			options.frac=[int(i) for i in options.frac.split(",")]
			if len(options.frac)!=2 : raise Exception
		except: 
			print "--frac should not be specified manually"
			sys.exit(1)
	else:
		if options.threads : nthreads=options.threads
		elif options.parallel!=None :
			if options.parallel[:7]!="thread:":
				print "ERROR: only thread:<n> parallelism supported by this program. It is i/o limited."
				sys.exit(1)
			nthreads=int(options.parallel[7:])
		else: nthreads=1
		
		options.frac=0,1

	try: options.step=[int(i) for i in options.step.split(",")]
	except:
		print "ERROR: Specify step as <first>,<last>,<step>"
		sys.exit(1)

	pid=E2init(sys.argv)

	# find the input files
	refineparms=js_open_dict(args[0]+"/0_refine_parms.json")
	inlst=refineparms["input"]
	if inlst[0][-4:]!=".lst" :
		print "Error: refine_xx must be run with a 'set' as --input following canonical EMAN2.1 guidelines"
		sys.exit(1)
	
	clsout=sorted([args[0]+"/"+i for i in os.listdir(args[0]) if "cls_result" in i])[-2:]
	if not "even" in clsout[0] : 
		print "ERROR: last 2 cls_result files not even/odd pair. Delete any incomplete iterations from refine folder!"
		sys.exit(1)

	if options.verbose: print "running on:",clsout

	#newproj="../"+os.getcwd().split("/")[-1]+"_m"
	#try: os.makedirs(newproj+"/particles")
	#except: pass

	lastloc=None
	lst=(LSXFile(inlst[0]),LSXFile(inlst[1]))	# Input particle "sets" in LSX files
	
	# This contains the classification results, which includes the orientation of the projection for each particle
	cls=(EMData.read_images(clsout[0]),EMData.read_images(clsout[1]))	# Generally small enough we can just read the whole thing
	
	# lstmap  maps (filename,n) to (e/o,set n)
	# allnames lists all files referenced in the sets. We make it a list so we can iterate sensibly
	lstmap={}
	allnames=set()
	for i in xrange(len(lst[0])): 
		lstmap[(lst[0][i][1],lst[0][i][0])]=(0,i)
		allnames.add(lst[0][i][1])
	for i in xrange(len(lst[1])): 
		lstmap[(lst[1][i][1],lst[1][i][0])]=(1,i)
		allnames.add(lst[0][i][1])
	
	allnames=list(allnames)
	allnames.sort()
	lst=None		# free up resources
	
	# Move the original files out of the way in the main thread
	if options.frac=0,1 :
		n=0
		for name in allnames:
			if options.filefilt!=None and not options.filefilt in name : continue
		
			base=base_name(name)
			if   os.path.exists("particles/{}.hdf".format(base)) : src="particles/{}.hdf".format(base)
			elif os.path.exists("particles/{}_ptcls.hdf".format(base)) : src="particles/{}_ptcls.hdf".format(base)
			dest="particles/{}__orig.hdf".format(base)
			try: 
				if os.path.exists(dest) : raise Exception
				os.rename(src,dest)
				if options.verbose>1: print "Renaming {} to {}".format(src,dest)
				file(src,"w").write(file(dest,"r").read())			# copy the original data back to the source file so we don't have gaps for unaligned particles, but only if the rename worked
				n+=1
			except: 
				if options.verbose>1: print "Failed to rename ",name
				pass
	
		if options.verbose==1: print n," stacks renamed to __orig"
	
	### Deal with threads (spawn more instances of ourselves as separate processes)
	if nthreads>1:
		print "Running in parallel with ",nthreads," threads"
		threads=[threading.Thread(target=os.system,args=[" ".join(sys.argv+["--frac={},{}".format(i,nthreads)])]) for i in xrange(nthreads)]
		for t in threads: t.start()
		for t in threads: t.join()
		print "Parallel fitting complete"
		sys.exit(0)
	
	### iterate over the particle files. We just skip any that aren't in the set that was refined
	for name in allnames[options.frac[0]:len(allnames):options.frac[1]]:
		base=base_name(name)
		db=js_open_dict(info_name(name))
		if options.verbose : print "### Processing {} ({})".format(base,options.frac[0]+1)
		
		movie="movieparticles/{}_ptcls.hdf".format(base)
		movieim=EMData(movie,0)
		movienfr=movieim["movie_frames"]  # number of frames in each movie for this stack
		movienptcl=EMUtil.get_image_count(movie)/movienfr		# number of particles in the frame
		
		# get CTF info for this micrograph. First try particle based, then resort to frame if necessary
		try: ctf=db["ctf"][0]
		except:
			try: ctf=db["ctf_frame"][1]
			except:
				print "ERROR: no CTF info for {}. Skipping file".format(name)
				continue
		
		# We need this to filter the projections
		#ctfflip=movieim.do_fft()		# we're just getting a complex image of the right size, a bit stupid way to handle it 
		#ctf.compute_2d_complex(ctfflip,Ctf.CtfType.CTF_FLIP)
		ctfim=movieim.do_fft()		# we're just getting a complex image of the right size, a bit stupid way to handle it 
		ctf.bfactor=50
		ctf.compute_2d_complex(ctfim,Ctf.CtfType.CTF_AMP)		# used to be _INTEN
		#ctfim.mult(ctfflip)		# an intensity image with phase flipping!
	
		# loop over the particles in this frame
		for n in xrange(movienptcl):
			# if we can't find the particle in the lst file
			try: eo,lstn=lstmap[(name,n)]
			except:
				if options.verbose>1 : print "skipping",name,n
				continue
			
			# read the frames for this particle, limited by --step
			if options.step[1]<=0 : end=movienfr+options.step[1]
			else: end=options.step[1]
			stack=EMData.read_images(movie,range(n*movienfr+options.step[0],n*movienfr+end,options.step[2]))
			if options.invert:
				for i in stack: i.mult(-1)
			
			# now find the correct reference projection
			projfsp=clsout[eo].replace("cls_result","projections")
			proj=EMData(projfsp,int(cls[eo][0][0,lstn]))	# projection image for this particle
			orient=Transform({"type":"2d","tx":0,"ty":0,"alpha":cls[eo][4][0,lstn],"mirror":int(cls[eo][5][0,lstn])})		# we want the alignment reference in the middle of the box
			proj.transform(orient)
			projf=proj.do_fft()
			projf.mult(ctfim)
			proj=projf.do_ift()		# now the projection has been filtered and has been rotated/flipped
			
			# We compute the CCF for the unaligned average, then filter out values close to the max
			# to define a region of permissible translation for individual frames
			unaliavg=sum(stack)
			ccfmask=unaliavg.calc_ccf(reff,EMAN2.fp_flag.CIRCULANT,True)
			ccfmask.process_inplace("normalize.edgemean")
			ccfmask.process_inplace("threshold.binary",{"value":ccfmask["maximum"]*.8})
			ccfmask.process_inplace("mask.addshells",{"nshells":2})
			
			avg=None
			atx=[]
			aty=[]
			atc=[]
			for i,im in enumerate(stack):
				ccf=im.calc_ccf(proj,EMAN2.fp_flag.CIRCULANT,True)
				ccf.mult(ccfmask)
				pk=ccf.calc_max_location()
				dx=-(pk[0]-nx/2)
				dy=-(pk[1]-ny/2)
				if options.verbose>1 : print base,i,dx,dy

				try: avg.add(im.process("xform.translate.int",{"trans":(dx,dy)}))
				except: avg=im.process("xform.translate.int",{"trans":(dx,dy)})
				
				atx.append(dx)
				aty.append(dy)
				atc.append(pk["maximum"])

			avg["movie_tx"]=atx
			avg["movie_ty"]=aty
			avg["movie_cc"]=atc
			avg.write_image("particles/{}_ptcls.hdf".format(base),n)
	

if __name__ == "__main__":
	main()
