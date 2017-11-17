#!/usr/bin/env python
from __future__ import print_function

#### python utilities. 
#### 2017-03

import numpy as np
import os
from EMAN2 import *

amino_dict= {0: 'ALA', 1: 'ARG', 2: 'ASN', 3: 'ASP', 4: 'CYS', 5: 'GLU', 6: 'GLN', 7: 'GLY', 8: 'HIS', 9: 'ILE', 10: 'LEU', 11: 'LYS', 12: 'MET', 13: 'PHE', 14: 'PRO', 15: 'SER', 16: 'THR', 17: 'TRP', 18: 'TYR', 19: 'VAL', 20: 'ASX', 21:'GLX'}
amino_dict.update(dict((v, k) for k, v in amino_dict.iteritems()))
amino_dict.update({'A': 0, 'C': 4, 'E': 5, 'D': 3, 'G': 7, 'F': 13, 'I': 9, 'H': 8, 'K': 11, 'M': 12, 'L': 10, 'N': 2, 'Q': 6, 'P': 14, 'S': 15, 'R': 1, 'T': 16, 'W': 17, 'V': 19, 'Y': 18, 'X':20})

def pdb2numpy(fname, readres=False, readocc=False, readbfac=False):
	f=open(fname,'r')
	lines=f.readlines()
	f.close()
	data=[]
	for l in lines:
		if l.startswith("ATOM") or l.startswith("HETATM"):
			if l[13:15]!="CA": continue
			atom=[l[30:38],l[38:46],l[46:54]]
			a=[float(a) for a in atom]
			if readres:
				#print l[17:20].strip()
				a.append(amino_dict[l[17:20].strip()])
			if readocc:
				a.append(float(l[54:60].strip()))
			if readbfac:
				a.append(float(l[60:66].strip()))
			data.append(a)
	
	pts=np.array(data)
	return pts

def numpy2pdb(data,fname,occ=[],bfac=[],chainid=[], model=0, residue=[]):
	if model>0:
		ww='a'
		#print "Appending.."
	else:
		ww='w'

	f=open(fname,ww)
	f.write("MODEL     %4d\n"%model)
	if len(occ)!=len(data):
		if len(occ)>0: print ("warning: occ and data not same size!")
		occ=np.zeros(len(data))
	if len(bfac)!=len(data):
		if len(bfac)>0: print ("warning: bfac and data not same size!")
		bfac=np.zeros(len(data)) 
	if len(chainid)!=len(data):
		if len(chainid)>0: print ("warning: chainid and data not same size!")
		chainid=np.zeros(len(data)) 
	if len(residue)!=len(data):
		if len(residue)>0: print ("warning: residue and data not same size!")
		residue=np.zeros(len(data)) 
	atomid=1
	curchain=chainid[0]
	for i,d in enumerate(data):
		if chainid[i]!=curchain: atomid=0
		f.write("ATOM {atomid:6d}  CA  {res} {chainid}{atomid:4d}    {px:8.3f}{py:8.3f}{pz:8.3f}{occ:6.2f}{bfac:6.2f}     S_00  0\n".format(atomid=atomid, chainid=chr(int(chainid[i])+65), px=d[0], py=d[1], pz=d[2], occ=occ[i], bfac=bfac[i], res=amino_dict[residue[i]]))
		atomid+=1
		curchain=chainid[i]

	f.write("TER  {:6d}      ALA {}{:4d}\n""".format(i+1, 'A', i))
	f.write("ENDMDL\n")
	f.close()

def norm_vec(vec):
	if len(vec.shape)==1:
		return vec/np.sqrt(np.sum(vec**2))
	else:
		return (vec.T/np.sqrt(np.sum(vec**2,axis=1))).T
	
	
def get_fft(img):
	return np.fft.fftshift(np.fft.fftn(np.fft.fftshift(img)))

def get_img(fft):
	return np.fft.ifftshift(np.fft.ifftn(np.fft.ifftshift(fft)).real)

### interpolate points. Same as np.interp, but the output can have >1 dimension
def interp_points(pts, npt=50, pmin=0., pmax=1.):
    pos=np.append(0,np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))
    fun_ax=interp1d(pos, pts.T, fill_value='extrapolate')
    mx=np.max(pos)
    rg=np.arange(npt,dtype=float)/(npt-1)*(pmax-pmin)*mx + pmin*mx
    ax=fun_ax(rg).T
    return ax

#### Distance from a point to a line segment
#### copied from stackoverflow..
def dist_line_point(A, B, P):
	""" segment line AB, point P, where each one is an array([x, y]) """
	if all(A == P) or all(B == P):
		return 0
	if np.arccos(np.dot((P - A) / numpy.linalg.norm(P - A), (B - A) / numpy.linalg.norm(B - A))) > np.pi / 2:
		return numpy.linalg.norm(P - A)
	if np.arccos(np.dot((P - B) / numpy.linalg.norm(P - B), (A - B) / numpy.linalg.norm(A - B))) > np.pi / 2:
		return numpy.linalg.norm(P - B)
	return numpy.linalg.norm(np.cross((P-A), (P-B))) / numpy.linalg.norm(A - B)

#### Distance from a set of points to a set of lines
#### Return the distance to the nearest line for each point
def dist_pts_lines(pts, lines):
	dsts=np.zeros((len(pts), len(lines)-1))
	for i,p in enumerate(pts):
		for j in range(len(lines)-1):
			dsts[i,j]=dist_line_point(lines[j], lines[j+1], p)
	return np.min(dsts, axis=1)

#### Moving average
def moving_average(a, n=3) :
	ret = np.cumsum(a, axis=0)
	ret[n:] = ret[n:] - ret[:-n]
	return ret[n - 1:] / n

#### Line to line distance and angle
def line2line_angle(a0, a1, b0, b1):
	a=a1-a0
	b=b1-b0
	c=b0-a0
	lang=np.dot(a,b)/(norm(a)*norm(b))
	return lang

	
#### Calculate the rotation matrix that rotate a given vector to [0,0,1]
def calc_rot_mat(v):

	tt=np.arctan2(v[2],v[1])
	rota=np.array([[1,0,0], [0, np.cos(tt), -np.sin(tt)], [0,np.sin(tt), np.cos(tt)]])
	vr=np.dot(v, rota)
	aa=np.arctan2(vr[1], vr[0])
	rotb=np.array([[np.cos(aa), -np.sin(aa), 0], [np.sin(aa), np.cos(aa),0],[0, 0, 1]])
	rot=np.dot(rota, rotb)
	m0=np.array([[0,0,1],[0,1,0],[1,0,0]])
	rot=np.dot(rot,m0)
	return rot

#### numpy version of EMAN2Ctf.compute_1d(). Takes vector of defocus input and output a matrix of CTF curves
def calc_ctf(defocus, bxsz=256, voltage=300, cs=4.7, apix=1. ,ampcnt=0.):
    
    
	b2=bxsz/2
	ds=1.0/(apix*bxsz)
	ns=min(int(np.floor(.25/ds)),bxsz/2)

	ctfout=np.zeros(b2)
	lbda = 12.2639 / np.sqrt(voltage * 1000.0 + 0.97845 * voltage * voltage)

	g1=np.pi/2.0*cs*1.0e7*pow(lbda,3.0);  
	g2=np.pi*lbda*defocus*10000.0;         
	acac=np.arccos(ampcnt/100.0);                 

	s=np.arange(b2, dtype=float)*ds
	gam=-g1*(s**4)+np.asarray(np.dot(np.asmatrix(g2).T, np.matrix(s**2)))
	ctfout = (np.cos(gam-acac))**2

	return ctfout


def make_missing_wedge(img, wedge=60):

	#img=img.transpose(0,1,2)
	ft=get_fft(img)
	ind=np.indices(ft.shape)-len(ft)/2
	tanx=np.arctan2(ind[2], ind[0])
	tanx=abs(abs(tanx)-np.pi/2)< (wedge/2)/180.*np.pi
	img2=get_img(ft*tanx)
	
	return img2


def idfft2(v,u,amp,phase,nx=256,ny=256,dtype=np.float32,usedegrees=False):
	"""
	Perform a vectorized, 2D discrete fourier transform. 
	Note that this approach scales poorly with box size.

	Author: Michael Bell (jmbell@bcm.edu)
	"""
	u = np.asarray(u).astype(dtype)
	v = np.asarray(v).astype(dtype)
	amp = np.asarray(amp).astype(dtype)
	phase = np.asarray(phase).astype(dtype)
	if usedegrees: phase *= np.pi/180.
	uu = nx*(u-u.min())/(u.max()-u.min())-nx/2.
	vv = ny*(v-v.min())/(v.max()-v.min())-ny/2.
	x,y=np.indices((nx,ny))
	xx = x-nx/2.
	yy = y-ny/2.
	o = np.ones((nx*ny))
	AA = np.multiply(amp.ravel()[:,np.newaxis],o[np.newaxis,:])
	pp = np.multiply(phase.ravel()[:,np.newaxis],o[np.newaxis,:])
	uuxx = np.multiply(uu.ravel()[:,np.newaxis],xx.ravel()[np.newaxis,:])
	vvyy = np.multiply(vv.ravel()[:,np.newaxis],yy.ravel()[np.newaxis,:])
	return np.sum(np.real(AA*np.exp(2*np.pi*1j*(uuxx+vvyy)+pp)).reshape(len(u),nx,ny),axis=0)


#makes a numbered series of subdirectories to compartmentalize results for spt programs when the same programs are run in the same parent directory
def makepath(options, stem='e2dir'):
	
	if not options.path:
		if options.verbose:

			print("\n(EMAN2_utils)(makepath), stem is", stem)
	
	elif options.path: 
		stem=options.path
	
	i=1
	while os.path.exists("{}_{:02d}".format(stem,i)): i+=1
	
	options.path="{}_{:02d}".format(stem,i)
	try: 
		os.mkdir(options.path)
	except: 
		pass
	
	return options


#runs commands at the commnad line for multiple spt programs
#def runcmd(options,cmd):
#	import subprocess
#	
#	p=subprocess.Popen( cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#	text=p.communicate()	
#	p.stdout.close()
#	
#	return 1

def runcmd(options,cmd,cmdsfilepath=''):
	if options.verbose > 9:
		print("\n(EMAN2_utils)(runcmd) running command {}".format(cmd))
	
	p=subprocess.Popen( cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	text=p.communicate()	
	p.stdout.close()
	
	if cmdsfilepath:
		with open(cmdsfilepath,'a') as cmdfile: cmdfile.write( cmd + '\n')

	if options.verbose > 8:
		print("\n(EMAN2_utils)(runcmd) done")

	return 1


def clip3d( vol, size ):
	
	volxc = vol['nx']/2
	volyc = vol['ny']/2
	volzc = vol['nz']/2
	
	Rvol =  Region( (2*volxc - size)/2, (2*volyc - size)/2, (2*volzc - size)/2, size , size , size)
	vol.clip_inplace( Rvol )
	#vol.process_inplace('mask.sharp',{'outer_radius':-1})
	
	return vol


def cmponetomany(reflist,target,align=None,alicmp=("dot",{}),cmp=("dot",{}), ralign=None, alircmp=("dot",{}),shrink=None,mask=None,subset=None,prefilt=False,verbose=0):
	"""Compares one image (target) to a list of many images (reflist). Returns """

	ret=[None for i in reflist]
#	target.write_image("dbug.hdf",-1)
	for i,r in enumerate(reflist):
		#print i,r
		if r[0]["sigma"]==0 : continue				# bad reference
		if subset!=None and i not in subset :
			ret[i]=None
			continue
		if prefilt :
			msk=r.process("threshold.notzero")					# mask from the projection
			r[0]=r[0].process("filter.matchto",{"to":target})
			r[0].mult(msk)											# remask after filtering

#		print "Final: ",target["source_n"],",",r[0]["source_n"]

		if align[0] :
			r[0].del_attr("xform.align2d")
			ta=r[0].align(align[0],target,align[1],alicmp[0],alicmp[1])
			if verbose>3: print(ta.get_attr("xform.align2d"))
			#ta.debug_print_params()

			if ralign and ralign[0]:
				if r[1]!=None :
					#print "(single) using mask, and ",mask
					ralign[1]["xform.align2d"] = ta.get_attr("xform.align2d").inverse()
					r[0].del_attr("xform.align2d")
					ralign[1]["mask"]=r[1]
					alip = target.align(ralign[0],r[0],ralign[1],alircmp[0],alircmp[1])
					ta=r[0].copy()
					ta.transform(alip["xform.align2d"].inverse())
					ta["xform.align2d"]=alip["xform.align2d"].inverse()
				else:
					ralign[1]["xform.align2d"] = ta.get_attr("xform.align2d")
					r[0].del_attr("xform.align2d")
					ta = r[0].align(ralign[0],target,ralign[1],alircmp[0],alircmp[1])

				if verbose>3: print(ta.get_attr("xform.align2d"))


			t =  ta.get_attr("xform.align2d")
			t.invert()
			p = t.get_params("2d")

			scale_correction = 1.0
			if shrink != None: scale_correction = float(shrink)

			if mask!=None :
				ta.mult(mask)
				ptcl2=target.copy()
				ptcl2.mult(mask)
				ret[i]=(ptcl2.cmp(cmp[0],ta,cmp[1]),scale_correction*p["tx"],scale_correction*p["ty"],p["alpha"],p["mirror"],p["scale"])
			else:
				try:
					ret[i]=(target.cmp(cmp[0],ta,cmp[1]),scale_correction*p["tx"],scale_correction*p["ty"],p["alpha"],p["mirror"],p["scale"])
				except:
					print("ERROR: CMP FAILURE. See err.hdf")
					print(cmp)
					target.write_image("err.hdf",0)
					ta.write_image("err.hdf",1)
					sys.exit(1)
					
#			ta.write_image("dbug.hdf",-1)

#				print ta["source_n"],target["source_n"]
				#psub=target.process("math.sub.optimal",{"ref":ta})
				#nout=ta["source_n"]*3
				#ta.write_image("dbug_%d.hdf"%target["source_n"],nout)
				#target.write_image("dbug_%d.hdf"%target["source_n"],nout+1)
				#psub.write_image("dbug_%d.hdf"%target["source_n"],nout+2)


		else :
			ret[i]=(target.cmp(cmp[0],r[0],cmp[1]),0,0,0,1.0,False)

		if verbose==3 : print(ret[i][0], end=' ')

	if verbose==3 : print("")
	if verbose==2 :
		print("Best: ",sorted([(ret[i][0],i) for i in range(len(ret))])[0])
	return ret





#used by some SPT programs (nov/2017); function might be deprecated or refactored in the near future
def sptOptionsParser( options, program='' ):
	
	print("\n(EMAN2_utils)(sptOptionsParser) parsing options")
	if program:
		print("from program {}".format(program))
	
	try:
		if options.align:
			#print "(e2spt_classaverage) --align to parse is", options.align
			options.align=parsemodopt(options.align)
		elif options.align == 'None' or  options.align == 'none':
			options.align=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --align not provided")
		
	try:
		if options.falign and options.falign != None and options.falign != 'None' and options.falign != 'none': 
			options.falign=parsemodopt(options.falign)
		elif options.falign == 'None' or  options.falign == 'none':
			options.falign=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --falign not provided")
	
	try:
		if options.aligncmp: 
			options.aligncmp=parsemodopt(options.aligncmp)
		elif options.aligncmp == 'None' or  options.aligncmp == 'none':
			options.aligncmp=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --aligncmp not provided")
	
	try:	
		if options.faligncmp: 
			options.faligncmp=parsemodopt(options.faligncmp)
		elif options.faligncmp == 'None' or  options.faligncmp == 'none':
			options.faligncmp=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --faligncmp not provided")
		
	try:
		if options.averager: 
			options.averager=parsemodopt(options.averager)
		elif options.averager == 'None' or  options.averager == 'none':
			options.averager=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --averager not provided")
		
	try:
		if options.autocenter:
			options.autocenter=parsemodopt(options.autocenter)
		elif options.autocenter == 'None' or  options.autocenter == 'none':
			options.autocenter=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --autocenter not provided")
		
	try:
		if options.autocentermask:
			options.autocentermask=parsemodopt(options.autocentermask)
		elif options.autocentermask == 'None' or  options.autocentermask == 'none':
			options.autocentermask=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --autocentermask not provided")
	
	try:
		if options.normproc and options.normproc != 'None' and options.normproc != 'none':
			options.normproc=parsemodopt(options.normproc)
		elif options.normproc == 'None' or  options.normproc == 'none':
			options.normproc=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --normproc not provided")
	
	try:
		if options.mask and options.mask != 'None' and options.mask != 'none':
			#print "\nparsing mask"
			#print "before = ".format(options.mask)
			options.mask = parsemodopt(options.mask)
			#print "after = ".format(options.mask)
		elif options.mask == 'None' or  options.mask == 'none':
			options.mask=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --mask not provided")
	
	try:	
		if options.preprocess and options.preprocess != 'None' and options.preprocess != 'none': 
			options.preprocess=parsemodopt(options.preprocess)
		elif options.preprocess == 'None' or  options.preprocess == 'none':
			options.preprocess=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --preprocess not provided")
	
	try:	
		if options.threshold and options.threshold != 'None' and options.threshold != 'none': 
			options.threshold=parsemodopt(options.threshold)
		elif options.threshold == 'None' or  options.threshold == 'none':
			options.threshold=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --threshold not provided")
	
	try:
		if options.preprocessfine and options.preprocessfine != 'None' and options.preprocessfine != 'none': 
			options.preprocessfine=parsemodopt(options.preprocessfine)
		elif options.preprocessfine == 'None' or  options.preprocessfine == 'none':
			options.preprocessfine=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --preprocessfine not provided")
	
	try:	
		if options.lowpass and options.lowpass != 'None' and options.lowpass != 'none': 
			options.lowpass=parsemodopt(options.lowpass)
		elif options.lowpass == 'None' or  options.lowpass == 'none':
			options.lowpass=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --lowpass not provided")
	
	try:
		if options.lowpassfine and options.lowpassfine != 'None' and options.lowpassfine != 'none': 
			options.lowpassfine=parsemodopt(options.lowpassfine)
		elif options.lowpassfine == 'None' or  options.lowpassfine == 'none':
			options.lowpassfine=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --lowpassfine not provided")
	
	try:
		if options.highpass and options.highpass != 'None' and options.highpass != 'none': 
			options.highpass=parsemodopt(options.highpass)
		elif options.highpass == 'None' or  options.highpass == 'none':
			options.highpass=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --highpass not provided")
	
	try:
		if options.highpassfine and options.highpassfine != 'None' and options.highpassfine != 'none': 
			options.highpassfine=parsemodopt(options.highpassfine)
		elif options.highpassfine == 'None' or  options.highpassfine == 'none':
			options.highpassfine=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --highpassfine not provided")
	try:
		if options.postprocess and options.postprocess != 'None' and options.postprocess != 'none': 
			options.postprocess=parsemodopt(options.postprocess)
		elif options.postprocess == 'None' or  options.postprocess == 'none':
			options.postprocess=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --postprocess not provided")
	
	try:
		if options.reconstructor and options.reconstructor != 'None' and options.reconstructor != 'none': 
			options.reconstructor=parsemodopt(options.reconstructor)
		elif options.reconstructor == 'None' or  options.reconstructor == 'none':
			options.reconstructor=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --reconstructor not provided")
	
	try:
		if options.preavgproc1 and options.preavgproc1 != 'None' and options.preavgproc1 != 'none': 
			options.preavgproc1=parsemodopt(options.preavgproc1)
		elif options.preavgproc1 == 'None' or  options.preavgproc1 == 'none':
			options.preavgproc1=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --reconstructor not provided")
		
	try:
		if options.preavgproc2 and options.preavgproc2 != 'None' and options.preavgproc2 != 'none': 
			options.preavgproc2=parsemodopt(options.preavgproc2)
		elif options.preavgproc2 == 'None' or  options.preavgproc2 == 'none':
			options.preavgproc2=None
	except:
		if options.verbose > 9:
			print("\nWARNING (might not be relevant): --reconstructor not provided")
	
	return options


'''
Used by many SPT programs. Function to write the parameters used for every run of the program to parameters.txt inside the path specified by --path.
Unfortunately, the usability of the .eman2log.txt file is limited when it is overcrowded with commands; e.g., a program that iteratively runs other EMAN2 programs at the command line
will SWARM the log file with commands that will obscure the command you wanted to log. Having a parameters file explicitly record what was the state of every parameter used by the program
is useful, as it also explicitly records values for parameters that were used by DEFAULT and not set by the user at the commnadline.
'''
def writeParameters( options, program, tag ):
	import datetime

	print("Tag received in writeParameters is {}".format(tag))

	names = dir(options)
	
	cmd = program
	lines = []
	now = datetime.datetime.now()
	lines.append(str(now)+'\n')
	
	#print "\nnames are", names
	optionscopy = options
	
	try:
		if options.search == 0 or options.search == 0.0:
			options.search = '0'
	except:
		pass
	try:
		if options.searchfine == 0 or options.searchfine == 0.0:
			options.searchfine = '0'
	except:
		pass
		
	#print "mask in write parameters is", optionscopy.mask, type(optionscopy.mask)
	for name in names:
				
		if getattr(options,name) and "__" not in name and "_" not in name:
		#if "__" not in name and "_" not in name:	
	
			#if "__" not in name and "_" not in name and str(getattr(options,name)) and 'path' not in name and str(getattr(options,name)) != 'False' and str(getattr(options,name)) != 'True' and str(getattr(options,name)) != 'None':			
			line = name + '=' + str(getattr(optionscopy,name))
					
			lines.append(line+'\n')
			
			if str(getattr(optionscopy,name)) != 'True' and str(getattr(optionscopy,name)) != 'False' and str(getattr(optionscopy,name)) != '':
			
				if name != 'parallel':
					if "{" in str( getattr(optionscopy,name) ) or "}" in  str(getattr(optionscopy,name)) or ")" in  str(getattr(optionscopy,name)) or ")"  in str(getattr(optionscopy,name)): 
						
						tail = str( getattr(optionscopy,name) ).replace(':','=').replace('(','').replace(')','').replace('{','').replace('}','').replace(',',':').replace(' ','').replace("'",'')
						if tail[-1] == ':':
							tail = tail[:-1] 
						cmd += ' --' + name + '=' + tail
					else:
						
						tail = str( getattr(optionscopy,name) )
						if tail[-1] == ':':
							tail = tail[:-1]
						cmd += ' --' + name + '=' + tail
						
				else:
					cmd += ' --' + name + '=' + str(getattr(optionscopy,name))
			
			elif str(getattr(optionscopy,name)) == 'True' or str(getattr(optionscopy,name)) == 'False':
				cmd += ' --' + name
	
	parmFile = 'parameters_' + tag + '.txt'
	lines.append('\n'+cmd+'\n')
	#f=open( optionscopy.path + '/' + parmFile,'w')
	pfile = optionscopy.path + '/' + parmFile
	f = open( pfile, 'w')
	f.writelines(lines)
	f.close()
	
	return cmd