#
# Author: Pawel A.Penczek, 09/09/2006 (Pawel.A.Penczek@uth.tmc.edu)
# Copyright (c) 2000-2006 The University of Texas - Houston Medical School
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
#
from EMAN2_cppwrap import *
from global_def import *

#  This file contains code under development or not currently used.

def ali2d_g(stack, outdir, maskfile= None, ir=1, ou=-1, rs=1, xr=0, yr=0, ts=1, center=1, maxit=10, CTF = False, snr = 1.):

	from utilities    import model_circle, combine_params2, dropImage, getImage, get_arb_params, center_2D
	from statistics   import aves, ave_oe_series, fsc, add_oe_series, ave_oe_series_g
	from alignment    import Numrinit, ringwe, Applyws, ali2d_sg
	from filter       import filt_from_fsc_bwt, filt_table, filt_ctf, filt_gaussinv
	from fundamentals import fshift, prepi
	from morphology   import ctf_2
	from math import exp
	import os
	if os.path.exists(outdir):  os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	first_ring=int(ir); last_ring=int(ou); rstep=int(rs); xrng=int(xr); yrng=int(yr); step=int(ts); max_iter=int(maxit);
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	nx = ima.get_xsize()
	# default value for the last ring
	if(last_ring ==- 1): last_ring = int(nx/2)-2
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask=getImage(maskfile)
		else: mask = maskfile
	else : mask = model_circle(last_ring,nx,nx)
	cnx = int(nx/2)+1
	cny = cnx
	mode = "F"
	low=.5
	if(CTF):
		parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
		ctf_params = get_arb_params(ima, parnames)
		data = []
		ctm = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
		lctf = len(ctm)
		ctf2 = []
		ctf2.append([0.0]*lctf)
		ctf2.append([0.0]*lctf)
		ctfb2 = [0.0]*lctf
		for im in xrange(nima):
			if(im > 0):
				ima = EMData()
				ima.read_image(stack,im)
				ctf_params = get_arb_params(ima, parnames)
				ctm = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			k = im%2
			for i in xrange(lctf):  ctf2[k][i] += ctm[i]
			if(ctf_params[6] == 0):
				from filter import filt_ctf
				ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
			data.append(ima)
		for i in xrange(lctf):
			ctfb2[i] = 1.0/(ctf2[0][i] + ctf2[1][i] + 1.0/snr)
			for k in xrange(2):
				ctf2[k][i] = 1.0/(ctf2[k][i] + 1.0/snr)

	numr = Numrinit(first_ring, last_ring, rstep, mode) 	#precalculate rings
	wr = ringwe(numr, mode)
	if(CTF):
		av1, av2 = add_oe_series(data)
		Util.add_img(av1, av2)
		from filter       import filt_table
		tavg = filt_table(av1, ctfb2)
	else:     tavg = aves(stack, "a")
	
	"""
	#tavg = filt_gaussinv(tavg, 0.3)
	#This part is a temporary measure
	noise_table = [0]*65
	noise_table_inv = [0]*65
	noise_table_inv2 = [0]*65
	k = 2.5
	for i in xrange(65):
		fre = i/64.0*0.5
		if i<32	: noise_table[i]=exp(-5.2983*fre+1.1513)
		else	: noise_table[i]=exp(-5.2983*k*fre+5.2983*0.25*(k-1)+1.1513)
		noise_table_inv[i]=1/noise_table[i]
		noise_table_inv2[i]=noise_table_inv[i]**2
	#tavg = filt_table(tavg, noise_table_inv2)	
	"""
	
	a0 = tavg.cmp("dot", tavg, {"negative":0, "mask":mask})
	print '%-15s = %-10.4g'%("Initial criterion",a0)	
	again = True
	cs = [0.0]*2
	if CTF == False:
		datap = []
		ima = EMData()
		for i in xrange(nima):
			ima.read_image(stack,i)
			o, kb = prepi(ima)
			datap.append(o)			
	for Iter in xrange(max_iter):
		if (CTF):
			ali2d_sg(datap, kb, numr, wr, cs, tavg, cnx, cny, xrng, yrng, step, mode, range(nima))
			av1, av2 = ave_oe_series_g(datap,kb)
			tavg = filt_table(Util.addn_img(av1, av2), ctfb2)
			av1 = filt_table(av1, ctf2[0])
			av2 = filt_table(av2, ctf2[1])
		else:
			ali2d_sg(datap, kb, numr, wr, cs, tavg, cnx, cny, xrng, yrng, step, mode, range(nima))
			av1, av2 = ave_oe_series_g(datap, kb)
			tavg = (av1*(int(nima/2)+(nima%2)) + av2*int(nima/2))/nima 
		frsc = fsc(av1, av2, 1.0, os.path.join(outdir, "drc%03d"%(Iter+1)))
		if center:
			# Potentially replace this:  						  
			cs = tavg.phase_cog()
			tavg = fshift(tavg, -cs[0], -cs[1])
			# tavg, cs[0], cs[1] = center_2D(tavg, center, last_ring)
		# a0 should increase; stop algorithm when it decreases.    
		a1 = tavg.cmp("dot", tavg, {"negative":0,"mask":mask})
		#if (a1 < a0):  break
		a0 = a1
		print "ITERATION #",Iter+1,"   criterion =",a0
		# Apply filter (FRC) to the reference image
		#fil_table=filt_from_fsc_bwt(frsc, low)
		#tavg=filt_table(tavg,fil_table)
		# write the current average
		
		# This is temp
		#tavg = filt_table(tavg, noise_table_inv2)
		# tavg = filt_gaussinv(tavg, 0.3)
		
		dropImage(tavg, os.path.join(outdir, "aqc_%03d.spi"%(Iter+1)),"s")
		
	for im in xrange(nima): 
		alpha  = datap[im].get_attr('alpha')
		sx     = datap[im].get_attr('sx')
		sy     = datap[im].get_attr('sy')
		mirror = datap[im].get_attr('mirror')
		ima = EMData()
		ima.read_image(stack, i, True)
		ima.set_attr_dict({"alpha":alpha, "sx":sx, "sy":sy, "mirror":mirror})
		ima.write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)

def ali2d_mg(stack, refim, outdir, maskfile = None, ir=1, ou=-1, rs=1, xr=0, yr=0, ts=1, center=1, maxit=10, CTF = False, snr = 1.):
# 2D multi-reference alignment using rotational ccf in polar coords and NUFT interpolation

	from utilities      import   model_circle, compose_transform2, combine_params2, dropImage, getImage
	from utilities	    import   center_2D, get_arb_params
	from statistics     import   fsc
	from alignment      import   Numrinit, ringwe, Applyws, ang_n
	from fundamentals   import   rtshg, fshift, prepi
	from morphology     import   ctf_2
	from random         import   randint
	from math 	    import   pi, cos, sin
	import os
	import sys
	
	first_ring=int(ir); last_ring=int(ou); rstep=int(rs); xrng=int(xr); yrng=int(yr); step=int(ts); max_iter=int(maxit);
	# create the output directory, if it does not exist
	if os.path.exists(outdir):  os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	output = sys.stdout
	nima = EMUtil.get_image_count(stack)
	ima  = EMData()
	ima.read_image(stack,0)
	# 
	nx=ima.get_xsize()
	# default value for the last ring
	if(last_ring == -1): last_ring=int(nx/2)-2

	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask=getImage(maskfile)
		else: mask = maskfile
	else : mask = model_circle(last_ring, nx, nx)
	#  references
	refi = []
	numref = EMUtil.get_image_count(refim)
	#  CTF stuff
	if(CTF):
		parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
		ctf_params = get_arb_params(ima, parnames)
		ctm = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
		lctf = len(ctm)
		ctf2 = [[[0.0]*lctf for k in xrange(2)] for j in xrange(numref)]
	# do the alignment
	# IMAGES ARE SQUARES!
	#  center is in SPIDER convention
	cnx = int(nx/2)+1
	cny = cnx

	mode = "F"
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr = ringwe(numr, mode)
	# reference images
	params = []
	# prepare the reference
	ima.to_zero()

	for j in xrange(numref):
		temp = EMData()
		temp.read_image(refim, j)
		#  even images, odd images, number of all images.  After frc, totav
		refi.append([temp, ima.copy(), 0])
	a0 = -1.
	Iter = 0
	while (Iter < max_iter):
		ringref = []
		for j in xrange(numref):
			refi[j][0].process_inplace("normalize.mask", {"mask":mask, "no_sigma":1})
			refip, kb = prepi(refi[j][0])
			cimage = Util.Polar2Dmi(refip, cnx, cny, numr, mode, kb)
			Util.Frngs(cimage, numr)
			Applyws(cimage, numr, wr)
			ringref.append(cimage)
			# zero refi
			refi[j][0].to_zero()
			refi[j][1].to_zero()
			refi[j][2] = 0
			if(CTF):
				for i in xrange(lctf): 
					ctf2[j][0][i] = 0.0
					ctf2[j][1][i] = 0.0
		assign = [[] for i in xrange(numref)]
		for im in xrange(nima):
			#
			ima = EMData()
			ima.read_image(stack, im)
			if(CTF):
				ctf_params = get_arb_params(ima, parnames)
				if(ctf_params[6] == 0):
					from filter import filt_ctf
					ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
			sx =  ima.get_attr('sx')
			sy =  ima.get_attr('sy')
			# align current image to the reference
			ima.process_inplace("normalize.mask", {"mask":mask, "no_sigma":0})
			imali,kb = prepi(ima)

			# [angt, sxst, syst, mirrort, xiref, peakt] = Util.multiref_polar_ali_2d(ima, ringref, xrng, yrng, step, mode, numr, cnx-sx, cny-sy)
			peak = -1.0E23
			nref = 0
			
			ky = int(2*yrng/step+0.5)/2
			kx = int(2*xrng/step+0.5)/2
			for i in xrange(-ky,ky+1):
				iy = i*step
				for j in xrange(-kx, kx+1):
					ix = j*step
					cimage = Util.Polar2Dmi(imali, cnx-sx+ix, cny-sy+iy, numr, mode, kb)
					Util.Frngs(cimage, numr)
					for iref in xrange(numref):
						retvals = Util.Crosrng_ms(ringref[iref], cimage, numr) 
						qn = retvals["qn"]
						qm = retvals["qm"]
						if qn >= peak or qm >= peak:
							sxt = -ix
							syt = -iy
							nref = iref
							if qn >= qm:
								angt = ang_n(retvals["tot"], mode, numr[len(numr)-1])
								peak = qn
								mirrort = 0
							else:
								angt = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
								peak = qm
								mirrort = 1
			co =  cos(angt*pi/180.0)
			so = -sin(angt*pi/180.0)
			sxst = sxt*co - syt*so
			syst = sxt*so + syt*co

			iref = nref
			# combine parameters and set them to the header, ignore previous angle and mirror
			[alphan, sxn, syn, mn] = combine_params2(0.0, sx, sy, 0, angt, sxst, syst, mirrort)
			#print  "combine with previous ",Iter,im,psin, sxn, syn, mn, iter
			ima.set_attr_dict({'alpha':alphan, 'sx':sxn, 'sy':syn, 'mirror':mn, 'ref_num':iref})
			ima.write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
			# apply current parameters and add to the average
			temp = rtshg(ima, alphan, sxn, syn)
			if mn: temp.process_inplace("mirror", {"axis":'x'})
			it = im%2
			Util.add_img( refi[iref][it], temp)
			if(CTF):
				ctm = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
				for i in xrange(lctf):  ctf2[iref][it][i] += ctm[i]
			assign[iref].append(im)
			refi[iref][2] += 1
			if(im%50 == 0):
				output.write( "\n" )
				output.write( " %6d " % im )
				output.flush()
			output.write( "." )
			output.flush( )
		output.write( "\n" )
		a1 = 0.0
		for j in xrange(numref):
			#print  "  ref ",j,refi[j][2]
			if(refi[j][2]<4):
				#ERROR("One of the references vanished","ali2d_m",1)
				#  if vanished, put a random image (only from main node!) there
				assign[j] = []
				assign[j].append( randint(0, nima-1))
				ima = EMData()
				ima.read_image(stack, assign[j][0])
				refi[j][0] = ima.copy()
				print "here we go"
			else:					
				if(CTF):
					for i in xrange(lctf):  ctm[i] = 1.0 / (ctf2[j][0][i] + 1.0/snr)
					from filter import filt_table
					av1 = filt_table( refi[j][0], ctm)
					for i in xrange(lctf):  ctm[i] = 1.0 / (ctf2[j][1][i] + 1.0/snr)
					av2 = filt_table( refi[j][1], ctm)
					frsc = fsc(av1, av2, 1.0, os.path.join(outdir,"drm%03d%04d"%(Iter, j)))
					#Now the total average
					for i in xrange(lctf):  ctm[i] = 1.0 / (ctf2[j][0][i] + ctf2[j][1][i] + 1.0/snr)
					refi[j][0] = filt_table( Util.addn_img( refi[j][0], refi[j][1] ), ctm)
				else:
					frsc = fsc(refi[j][0], refi[j][1], 1.0, os.path.join(outdir,"drm%03d%04d"%(Iter, j)))
					Util.add_img( refi[j][0], refi[j][1] )
					Util.mul_scalar( refi[j][0], 1.0/float(refi[j][2]) )
			if center>0:
				refi[j][0], shiftx, shifty = center_2D(refi[j][0], center, last_ring)
			# write the current average
			TMP = []
			for i_tmp in xrange(len(assign[j])):
				TMP.append(float(assign[j][i_tmp]))
			TMP.sort()
			refi[j][0].set_attr_dict({'ave_n': refi[j][2],  'members': TMP })
			del TMP
			# replace the name of the stack with reference with the current one
			newrefim = os.path.join(outdir,"aqm%03d.hdf"%Iter)
			refi[j][0].write_image(newrefim, j)
			a1 += refi[j][0].cmp("dot", refi[j][0], {"negative":0, "mask":mask})
		Iter += 1
		print '%-15s %5d %-15s = %10.4g'%("ITERATION #",Iter,"criterion",a1)
		if(a1 > a0):  a0 = a1
		else:
			os.system('cp '+newrefim+' multi_ref.hdf')
			break
			
def ali2d_sg(data, kb, numr, wr, cs, tavg, cnx, cny, xrng, yrng, step, mode, list_p=[]):
	"""
		single iteration alignment using ormy3g
	"""
	from utilities import compose_transform2, combine_params2
	from fundamentals import prepi
	
	# 2D alignment using rotational ccf in polar coords and NUFT interpolation
	tavgi, kb = prepi(tavg)
	cimage = Util.Polar2Dmi(tavgi, cnx, cny, numr, mode, kb)
	Util.Frngs(cimage, numr)
	Applyws(cimage, numr, wr)

	# align all images
	if(len(list_p) == 0):
		list_p = range(len(data))
	for imt in list_p:
		alpha  = data[imt].get_attr('alpha')
		sx     = data[imt].get_attr('sx')
		sy     = data[imt].get_attr('sy')
		mirror = data[imt].get_attr('mirror')
		if mirror: alpha, sx, sy, scale = compose_transform2(alpha, sx, sy, 1.0, 0, cs[0], -cs[1], 1.0)
		else:	   alpha, sx, sy, scale = compose_transform2(alpha, sx, sy, 1.0, 0, -cs[0], -cs[1], 1.0)
		[angt, sxst, syst, mirrort, peakt] = ormy3g(data[imt], kb, cimage, xrng, yrng, step, mode, numr, cnx-sx, cny-sy)
		[alphan, sxn, syn, mn] = combine_params2(0.0, sx, sy, 0, angt, sxst, syst, mirrort)
		data[imt].set_attr_dict({'alpha':alphan, 'sx':sxn, 'sy':syn, 'mirror':mn})


def ali_param_3d_to_2d(stack):
	from utilities import get_arb_params, set_arb_params, ali_params_3D_2D
	import types 
	parameters_2D_name=["alpha", "sx",    "sy",  "mirror" ]
	parameters_3D_name=[ "phi",  "theta", "psi", "s2x", "s2y" ]
	if(type(stack) == types.StringType): 
		nima = EMUtil.get_image_count(stack)
		for im in xrange(nima):
			if( type(stack) == types.StringType ): ima.read_image(stack,im)
			parameters_3D = get_arb_params(ima, parameters_3D_name)
			alpha, sx, sy, mirror = ali_params_3D_2D(parameters_3D[0],parameters_3D[1],parameters_3D[2],parameters_3D[3],parameters_3D[4],parameters_3D[5])
			set_arb_params( ima, [ alpha, sx, sy, mirror ], parameters_2D_name)
			ima.write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	else:
		for im in xrange(len(stack)):
			parameters_3D = get_arb_params(stack[im], parameters_3D_name)
			alpha, sx, sy, mirror = ali_params_3D_2D(parameters_3D[0],parameters_3D[1],parameters_3D[2],parameters_3D[3],parameters_3D[4],parameters_3D[5])
			set_arb_params( stack[im], [ alpha, sx, sy, mirror ], parameters_2D_name)

def ali_param_2d_to_3d(stack):
	import os
	from utilities import compose_transform2
	from utilities import get_arb_params, set_arb_params
	
	""" 
		transform 2D alignment parameters into 3D alignment parameters.	
		has to be used if no 3D aligment parameters have been determined yet.

	"""
	dummy = EMData()
	header_3d_ID=["alpha","sx","sy","mirror", "psi","theta","phi","s2x","s2y"]
	header_2d_ID=["alpha","sx","sy","mirror"]
	nima = EMUtil.get_image_count(stack)
	for i in xrange(nima):
		dummy.read_image(stack,i, True)
		param_2d=get_arb_params(dummy,header_2d_ID)
		alphan,s2x, s2y,scalen = compose_transform2(0,param_2d[1], param_2d[2], 1, -param_2d[0], 0, 0, 1)
		if( param_2d[3] > 0.5 ) :
			phi   = 180.0
			theta = 180.0
			psi   = (540.0 + alphan)%360.0
		else:
			psi   = (alphan)%360.0
			phi   = 0.0
			theta = 0.0
		params=[ 0., 0., 0., 0, psi, theta, phi, s2x, s2y]
		set_arb_params(dummy, params, header_3d_ID)
		dummy.write_image(stack,i, EMUtil.ImageType.IMAGE_HDF, True)


'''	NOT USED
def ali2d_r(stack, outdir, ir=1, ou=-1, rs=1, center=1, maxit=10):
# 2D alignment using rotational ccf in polar coords and quadratic interpolation
	from utilities import model_circle, compose_transform2, combine_params2, dropImage, start_time, finish_time
	from fundamentals import rot_shift2D
	from statistics import aves, fsc, ave_oe_series
	from alignment import Numrinit, ringwe, Applyws, ang_n
	from filter import fshift
	import os
	from EMAN2 import EMUtil,EMData
	tt =start_time()
	first_ring=int(ir)
	last_ring=int(ou)
	rstep=int(rs)
	max_iter = int(maxit)
	# create the output directory, if it does not exist
	if os.path.exists(outdir) is False: os.mkdir(outdir)
	# reading image and gethering the information
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	nx=ima.get_xsize()
	# default value for the last ring
	if(last_ring==-1): last_ring=nx-2
	mask = model_circle(last_ring,nx,nx)
	# calculate total average using current alignment parameters - 'aves' function removed
	tave = aves(stack)
	a0 = tave.cmp("dot", tave, {"negative":0,"mask":mask})
	print  "Initial criterion=",a0
	#  center is in SPIDER convention
	cnx = int(nx/2)+18
	cny = cnx
	mode = "F"
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr   = ringwe(numr, mode)
	again = True
	cs = [0.0]*2  # additional shifts from the centering of the average (if requested) from the previous iteration
	#iteration
	for iter in xrange(max_iter):
		#prepare the reference
		cimage=Util.Polar2Dm(tave, cnx, cny, numr, mode)
		Util.Frngs(cimage, numr)
		Applyws(cimage, numr, wr)
		# prepare the images and align them
		for im in xrange(nima):
			# get image & params.
			ima = EMData()
			ima.read_image(stack,im)
			alpah = ima.get_attr('alpha')
			sx =  ima.get_attr('sx')
			sy =  ima.get_attr('sy')
			mirror =  ima.get_attr('mirror')
			#  add centering from the previous iteration, if image was mirrored, filp the sign of x center
			if mirror: alpha, sx, sy, scale = compose_transform2(alpha, sx, sy, 1.0, 0.0,  cs[0], -cs[1], 1.0)
			else:      alpha, sx, sy, scale = compose_transform2(alpha, sx, sy, 1.0, 0.0, -cs[0], -cs[1], 1.0)
			# align current image to the reference
			peak = -1.0E23
			cimage_o=Util.Polar2Dm(ima, cnx-sx, cny-sy, numr, mode)
			Util.Frngs(cimage_o, numr)
			retvals = Util.Crosrng_ms(cimage, cimage_o, numr)
			qn = retvals["qn"]
			qm = retvals["qm"]
			if(qn >=peak or qm >=peak):
				if (qn >= qm):
					angt = ang_n(retvals["tot"], mode, numr[len(numr)-1])
					peak=qn
					mirror=0
				else:
					angt = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
					peak=qm
					mirror=1
			angt = ang_n(retvals["tot"], mode, numr[len(numr)-1])		
			# combine parameters and set them to the header, ignore previous angle and mirror
			[alphan, sxn, syn, mn] = combine_params2(0.0, sx, sy, 0, angt, 0, 0, mirror)
			#print  "combine with previous ",iter,im,psin, sxn, syn, mn
			ima.set_attr_dict({'alpha':alphan, 'sx':sxn, 'sy':syn,'mirror':mn})
			ima.write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
			
		av1,av2 = ave_oe_series(stack) # odd, even averages.
		frsc = fsc(av1, av2, 1.0, os.path.join(outdir, "drc%03d"%iter))
		if center:
			# Center.
			av1 = (av1*(int(nima/2)+(nima%2)) + av2*int(nima/2))/nima
			# Potentially replace this:
			cs = av1.phase_cog()
			#print  "SHIFT ",cs
			tave = fshift(av1, -cs[0], -cs[1])
		else:
			tave = (av1*(int(nima/2)+(nima%2)) + av2*int(nima/2))/nima
		# a0 should increase; stop algorithm when it decreases.
		a0 = tave.cmp("dot", tave, {"negative":0,"mask":mask}) # tave' * tave
		print'%-15 %5d %15 = %10.g'%(" ITERATION #",iter+1,"criterion",a0)
		# write the current average
		dropImage(tave, os.path.join(outdir, "aqc%03d.spi"%iter))
	print finish_time(tt)
'''
'''	Not used anywhere
def ali3d_b(stack, ref_vol, outdir, maskfile = None,ir=1, ou=-1, rs=1, xr=0, yr=0,
	    ts=1, dtheta=15, maxit=10, ref_a="S", sym="c1", CTF = None):  
    # 2D alignment using rotational ccf in polar coords and gridding
    # interpolation 
    
	from utilities      import model_circle, dropImage
	from alignment      import proj_ali
	from reconstruction import recons3d_4nn_ctf, recons3d_4nn
	from statistics     import fsc
	from filter         import filt_params, filt_btwl
	import os
	snr=1.
	sign=1

	first_ring = int(ir);    last_ring = int(ou); rstep = int(rs); 
	xrng       = int(xr);    yrng      = int(yr); step  = int(ts);
	max_iter   = int(maxit); 
	# create the output directory, if it does not exist
	if os.path.exists(outdir) is False: os.mkdir(outdir)
	nima = EMUtil.get_image_count(stack)
	#  compare the image size
	vol = EMData()
	vol.read_image(stack,0)
	nx = vol.get_xsize()
	#vol.read_image(ref_vol)
	# default value for the last ring
	if(last_ring==-1): last_ring=nx-2
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask3D=getImage(maskfile)
		else: mask3D = maskfile
	else: mask3D = model_circle(last_ring, nx, nx, nx)
	#mask2D = model_circle(last_ring, nx, nx, 1)
    
	# do the projection matching
	# begin a refinement loop, slowly decrease dtheta inside the loop
	for iter in xrange(max_iter):
		print " ali3d_b: ITERATION #",iter
		proj_ali(ref_vol, mask3D, stack, first_ring, last_ring, rstep, xrng, yrng, step, dtheta, ref_a, sym, CTF)

		# resolution
		list_p = range(0,nima,2)
		if(CTF): vol1 = recons3d_4nn_ctf(stack, list_p, snr, sign, sym)
		else:    vol1 = recons3d_4nn(stack, list_p, sym)

		list_p = range(1,nima,2)
		if(CTF): vol2 = recons3d_4nn_ctf(stack, list_p, snr, sign, sym)
		else:    vol2 = recons3d_4nn(stack, list_p, sym)

		[mean, sigma, xmin, xmax ] =  Util.infomask(vol1, mask3D, false)
		vol1 = (vol1-mean)*mask3D                                    #use processor instead
		[mean, sigma, xmin, xmax ] =  Util.infomask(vol2, mask3D)
		vol2 = (vol2-mean)*mask3D

		res = fsc(vol1, vol2, 1.0, os.path.join(outdir,"dres%03d"%iter))
		del vol1
		del vol2
		
		# calculate new and improved 3D
		list_p = range(nima)
		if(CTF): vol = recons3d_4nn_ctf(stack, list_p, snr, sign, sym)
		else:    vol = recons3d_4nn(stack, list_p, sym)
		# store the reference volume
		dropImage(vol,os.path.join(outdir,"vol%03d.spi"%iter))

		# here figure the filtration parameters and filter vol for the
		# next iteration
		fl, fh = filt_params(res)
		vol    = filt_btwl(vol, fl, fh)
		# store the filtred reference volume
		dropImage(vol, os.path.join(outdir, "volf%03d.spi"%iter))
		#  here the loop should end
	return vol
'''

''' 	        
def ali3d_e_iter(stack, mask3d, iteration, defocus, ptl_defgrp, radius, lowf, highf, snr, dtheta, symmetry):

	"""
		3D alignment inner loop 
	"""
	
	import os
	from statistics import fsc
	from filter     import filt_btwl, filt_ctf
	from projection import prep_vol
	from utilities  import amoeba, info
	from math       import pi,sin
	
	img=EMData()	
	firstp=0
	lastp = 0
	sign=1.
	par_str=["s2x", "s2y", "psi", "theta", "phi"]
	par_str1=["psi", "theta", "phi", "s2x", "s2y"]
	ctf_par=["Pixel_size", "Cs", "voltage"]
	fdres_pat="dres{***}"
	nl = EMUtil.get_image_count(stack)
	img.read_image(stack,0)
	[Pixel_size,cs,voltage] = get_arb_params(img,ctf_par)
	for mic in range(len(ptl_defgrp)):
		iteration += 1
		lastp += ptl_defgrp[mic]
		list_of_particles=range(firstp,lastp)
		# Calculate reconstruction using particles NOT in the current group					  	  
		list_p = range(nl)
		for e in list_of_particles:  list_p.remove(e)								  	  
		vol = recons3d_4nn_ctf(stack,list_p, snr, sign, symmetry)
		vol_ctf = filt_ctf(vol, defocus[mic], cs, voltage, Pixel_size)
		vol = filt_btwl(vol_ctf, lowf, highf)
		vol*=mask3d
		data=[]
		volft,kb=prep_vol(vol)
		data.insert(0,volft)
		data.insert(1,kb)
		data.insert(3,mask3d)
		for imn in range(ptl_defgrp[mic]):
			img.read_image(stack, list_of_particles[imn])
			data.insert(2,img)
			atparams = get_arb_params(img,par_str1)
			initial = eqproj(atparams,data)
			stheta  = abs(sin(atparams[1]*pi/180.0))
			if(stheta >0.0): weight_phi=min(180.0,dtheta/stheta/2.0)
			else: weight_phi=180.0
			from utilities import start_time, finish_time
			t3=start_time()
			optm_params =  amoeba(atparams, [weight_phi,dtheta,weight_phi,1.0,1.0],eqproj, 1.e-4,1.e-4,500,data)
			del  data[2]
			tmp_params = [optm_params[0][3],optm_params[0][4],optm_params[0][0],optm_params[0][1],optm_params[0][2]]
			update_attrt(img,par_str,tmp_params,"r")
			t4 = finish_time(t3)
			img.write_image(stack, list_of_particles[imn], EMUtil.ImageType.IMAGE_HDF, True)
		firstp=lastp
		# after all groups have been processed, calculate the current resolution
		# for the time being, do it after each iteration
		list_p = range(0,nl,2)
		vol1=recons3d_4nn_ctf(stack, list_p, snr, sign, symmetry)
		#dropImage(vol1,"Cnvolcmm1.spi")
		list_p = range(1,nl,2)
		vol2=recons3d_4nn_ctf(stack, list_o, snr, sign, symmetry)
		vol1 *= mask3d
		vol2 *= mask3d
		fdres = parse_spider_fname(fdres_pat, iteration)							  	  
		fsc(vol1, vol2, 1.0, fdres)		 										  	  											  	  
	return  iteration

	
def update_attrt(img, par_str, params, opt="s"):	
	"""
		Update attributes stored in the headers
		1. subtract new
		2. replaced by new
		3. add new
	"""
	old_params = get_arb_params(img,par_str)
	for i in xrange(len(par_str)):
		if(opt == "s"): old_params[i]-=params[i]
		if(opt == "r"): old_params[i]=params[i]
		if(opt == "a"): old_params[i]+=params[i]
	set_arb_params(img, old_params, par_str)
	del old_params


def ali3d_e(stack, maskfile, radius=25, snr=1.0, lowf=.25, highf=.3, max_it=10, dtheta=2, symmetry="c1", CTF = None):
	"""
		
	"""
	nl = EMUtil.get_image_count(stack) # check the data, and get defocus
	img = EMData()
	defocus = []
	ptl_defgrp = []  	 
	par_str = ["defocus","defgrp"]
	ptl_num_def = 0
	def_num = -1
	for i in xrange(nl):
		img.read_image(stack,i)		 
		tmp_params = get_arb_params(img, par_str)
		if(i==0):
			nx = img.get_xsize()		 
			defocus.append(tmp_params[0])
			def_num += 1
		if(tmp_params[1]!=def_num): 
			defocus.append(tmp_params[0])
			ptl_defgrp.append(ptl_num_def) 
			def_num+=1
			ptl_num_def=0
		ptl_num_def+=1
	ptl_defgrp.append(ptl_num_def)
	iteration=-1
	if os.path.exists(maskfile): mask3D=getImage(maskfile)
	else : mask3d=model_circle(radius, nx, nx, nx)
	for dummy in xrange(1000): # fake loop
		if(iteration <= max_it): iteration=ali3d_e_iter(stack,mask3d,iteration,defocus,ptl_defgrp,radius,lowf,highf,snr,dtheta,symmetry)		
'''

"""
This is not used, mainly because it is not parallelizable.
def ali2d_b(stack, outdir, maskfile=None, ir=1, ou=-1, rs=1, xr=0, yr=0, ts=1, center=1, maxit=10):
# 2D alignment using rotational ccf in polar coords and gridding interpolation

	import os
	from utilities import model_circle, compose_transform2, combine_params2, dropImage, info
	from statistics import aves, fsc, ave_var_series_g, ave_oe_series_g
	from alignment import Numrinit, ringwe, Applyws, ormqip, kbt, ormy3
	from fundamentals import prepg, rtshgkb, fshift
	from filter import filt_from_fsc_bwt, filt_table
	#from string import *

	first_ring=int(ir); last_ring=int(ou); rstep=int(rs); xrng=int(xr); yrng=int(yr); step=int(ts); max_iter=int(maxit);
	
	if os.path.exists(outdir) : os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	
	nima = EMUtil.get_image_count(stack)
	temp = EMData()
	temp.read_image(stack,0)

	# prepare KB interpolants
	nx=temp.get_xsize()
	kb = kbt(nx)

	# default value for the last ring
	#if(last_ring==-1): last_ring=nx-2
	if last_ring == -1 : last_ring=int(nx/2)-2

	# read images and prepare them for gridding
	data = []
	for im in xrange(nima):
		if(im>0):
			temp = EMData()
			temp.read_image(stack,im)
		alpha = temp.get_attr('alpha')
		sx =  temp.get_attr('sx')
		sy =  temp.get_attr('sy')
		mn =  temp.get_attr('mirror')
		data.append(prepg(temp,kb))
		data[im].set_attr_dict({'alpha':alpha, 'sx':sx, 'sy':sy, 'mirror': mn})
	if maskfile==None : mask = model_circle(last_ring,nx,nx)
	else              : getImage(maskfile)
	
	# calculate total average using current alignment parameters
	tave,tvar = ave_var_series_g(data,kb)
	#dropImage(tave,"a1.spi")
	#dropImage(tvar,"a2.spi")
	a0 = tave.cmp("dot", tave, {"negative":0, "mask":mask})
	print  "Initial criterion=",a0
	
	# do the alignment
	# IMAGES ARE SQUARES!
	#  center is in SPIDER convention
	cnx = int(nx/2)+1
	cny = cnx

	mode = "F"
	#precalculate rings
	numr=Numrinit(first_ring,last_ring,rstep,mode)
	wr=ringwe(numr,mode)
	
	for iter in xrange(max_iter):
		again = False
		for im in xrange(nima):
			# subtract current image from the average
			alpha = data[im].get_attr('alpha')
			sx =  data[im].get_attr('sx')
			sy =  data[im].get_attr('sy')
			mirror =  data[im].get_attr('mirror')
			temp = rtshgkb(data[im], alpha, sx, sy, kb)
			if  mirror: temp.process_inplace("mirror",{"axis":'x'})

			#  Subtract current image from the average
			refim = tave - temp/nima
			refim_p = prepg(refim,kb)
			cimage=Util.Polar2Dmi(refim_p,cnx,cny,numr,mode,kb)
			Util.Frngs(cimage, numr)
			Applyws(cimage, numr, wr)

			# align current image to the reference minus this image
			[angt,sxst,syst,mirrort,peakt]=ormy3(temp,cimage,xrng,yrng,step,mode,numr,cnx,cny,"gridding")			
			# print angt, sxst, syst, mirrort, peakt
			#[angt,sxst,syst,mirrort,peakt]=ormqip(prepg(temp,kb),cimage,xrng,yrng,step,mode,numr,kb,cnx,cny,nx)			
			# print angt, sxst, syst, mirrort, peakt

			# combine parameters and set them to the header
			[angn,sxn,syn,mn]=combine_params2(alpha, sx, sy, mirror, angt, sxst, syst, mirrort)

			# apply params to the image
			temp = rtshgkb(data[im], angn, sxn, syn, kb)
			if  mn: temp.process_inplace("mirror",{"axis":'x'})

			# check whether the criterion actually increased
			# add current image to the average
			temp = refim + temp/nima

			# calculate the criterion
			a1 = temp.cmp("dot", temp, {"negative":0, "mask":mask})
			print a1, angn, sxn, syn, mn
			if a1 > a0:
				#print  im,"  ",a1,"  ",mirror,"  ",mirrort,"  ",psi,"  ",angt,"  ",sxst,"  ",syst
				# replace the average by the improved average and set the new parameters to the image, otherwise, do nothing
				tave = temp.copy()
				data[im].set_attr_dict({'alpha':angn, 'sx':sxn, 'sy':syn,'mirror': mn})
				a0 = a1
				again = True
		if again :
			# calculate total average using current alignment parameters
			print " ITERATION #",iter,"  criterion = ",a0
			av1,av2 = ave_oe_series_g(data,kb)
			frsc = fsc(av1,av2,1.0,os.path.join(outdir,"drm%03d"%iter))
			if center:
				#center
				av1 = (av1*(int(nima/2)+(nima%2)) + av2*int(nima/2))/nima
				s = av1.phase_cog()
				tave = fshift(av1, -s[0], -s[1])
				for im in xrange(nima):
					alpha = data[im].get_attr('alpha')
					sx =  data[im].get_attr('sx')
					sy =  data[im].get_attr('sy')
					alphan,sxn,syn,scale = compose_transform2(alpha, sx, sy, 1.0, 0.0, -s[0], -s[1], 1.0)
					data[im].set_attr_dict({'alpha':alphan, 'sx':sxn, 'sy':syn})
			else:
				tave = (av1*(int(nima/2)+(nima%2)) + av2*int(nima/2))/nima
			# write the current average
			# fil_table=filt_from_fsc_bwt(frsc, low=0.5)
			# tave=filt_table(tave,fil_table)
			dropImage(tave,os.path.join(outdir,"aqm%03d.spi"%iter),"s")
		else:
			break

	for im in xrange(nima):
		temp.read_image(stack,im)
		alpha = data[im].get_attr('alpha')
		sx =  data[im].get_attr('sx')
		sy =  data[im].get_attr('sy')
		mn =  data[im].get_attr('mirror')
		temp.set_attr_dict({'alpha':alpha, 'sx':sx, 'sy':sy,'mirror': mn})
		temp.write_image(stack,im)
	#for im in xrange(nima): data[im].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	return	

def ali2d_b2(stack, outdir, maskfile=None, ir=1, ou=-1, rs=1, xr=0, yr=0, ts=1, center=1, maxit=10):
# 2D alignment using rotational ccf in polar coords and gridding interpolation

	import os
	from utilities import model_circle, compose_transform2, combine_params2, dropImage, info
	from statistics import aves, fsc, ave_var_series_g, ave_oe_series_g
	from alignment import Numrinit, ringwe, Applyws, ormqip, kbt, ormy3
	from fundamentals import prepg, rtshgkb, fshift
	from filter import filt_from_fsc_bwt, filt_table
	#from string import *

	first_ring=int(ir); last_ring=int(ou); rstep=int(rs); xrng=int(xr); yrng=int(yr); step=int(ts); max_iter=int(maxit);
	
	if os.path.exists(outdir) : os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	
	nima = EMUtil.get_image_count(stack)
	temp = EMData()
	temp.read_image(stack,0)

	# prepare KB interpolants
	nx=temp.get_xsize()
	kb = kbt(nx)

	# default value for the last ring
	#if(last_ring==-1): last_ring=nx-2
	if last_ring == -1 : last_ring=int(nx/2)-2

	# read images and prepare them for gridding
	data = []
	for im in xrange(nima):
		if(im>0):
			temp = EMData()
			temp.read_image(stack,im)
		alpha = temp.get_attr('alpha')
		sx =  temp.get_attr('sx')
		sy =  temp.get_attr('sy')
		mn =  temp.get_attr('mirror')
		data.append(prepg(temp,kb))
		data[im].set_attr_dict({'alpha':alpha, 'sx':sx, 'sy':sy, 'mirror': mn})
	if maskfile==None : mask = model_circle(last_ring,nx,nx)
	else              : getImage(maskfile)
	
	# calculate total average using current alignment parameters
	tave,tvar = ave_var_series_g(data,kb)
	#dropImage(tave,"a1.spi")
	#dropImage(tvar,"a2.spi")
	a0 = tave.cmp("dot", tave, {"negative":0, "mask":mask})
	print  "Initial criterion=",a0
	
	# do the alignment
	# IMAGES ARE SQUARES!
	#  center is in SPIDER convention
	cnx = int(nx/2)+1
	cny = cnx

	mode = "F"
	#precalculate rings
	numr=Numrinit(first_ring,last_ring,rstep,mode)
	wr=ringwe(numr,mode)
	
	for iter in xrange(max_iter):
		again = False
		refim = tave
		refim_p = prepg(refim,kb)
		cimage=Util.Polar2Dmi(refim_p,cnx,cny,numr,mode,kb)
		Util.Frngs(cimage, numr)
		Applyws(cimage, numr, wr)
		a2 = a0
		for im in xrange(nima):
			# subtract current image from the average
			alpha = data[im].get_attr('alpha')
			sx =  data[im].get_attr('sx')
			sy =  data[im].get_attr('sy')
			mirror =  data[im].get_attr('mirror')
			temp = rtshgkb(data[im], alpha, sx, sy, kb)
			if  mirror: temp.process_inplace("mirror",{"axis":'x'})

			# align current image to the reference minus this image
			[angt,sxst,syst,mirrort,peakt]=ormy3(temp,cimage,xrng,yrng,step,mode,numr,cnx,cny,"gridding")			

			# combine parameters and set them to the header
			[angn,sxn,syn,mn]=combine_params2(alpha, sx, sy, mirror, angt, sxst, syst, mirrort)

			# apply params to the image
			temp = rtshgkb(data[im], angn, sxn, syn, kb)
			if  mn: temp.process_inplace("mirror",{"axis":'x'})

			# calculate the criterion
			a1 = temp.cmp("dot", tave, {"negative":0, "mask":mask})
			print a1, angn, sxn, syn, mn
			if a1 > a0:
				# replace the average by the improved average and set the new parameters to the image, otherwise, do nothing
				tave = temp.copy()
				data[im].set_attr_dict({'alpha':angn, 'sx':sxn, 'sy':syn,'mirror': mn})
				if a1>a2 : a2 = a1
				again = True
		a0 = a2
		if again :
			# calculate total average using current alignment parameters
			print " ITERATION #",iter,"  criterion = ",a0
			av1,av2 = ave_oe_series_g(data,kb)
			frsc = fsc(av1,av2,1.0,os.path.join(outdir,"drm%03d"%iter))
			if center:
				#center
				av1 = (av1*(int(nima/2)+(nima%2)) + av2*int(nima/2))/nima
				s = av1.phase_cog()
				tave = fshift(av1, -s[0], -s[1])
				for im in xrange(nima):
					alpha = data[im].get_attr('alpha')
					sx =  data[im].get_attr('sx')
					sy =  data[im].get_attr('sy')
					alphan,sxn,syn,scale = compose_transform2(alpha, sx, sy, 1.0, 0.0, -s[0], -s[1], 1.0)
					data[im].set_attr_dict({'alpha':alphan, 'sx':sxn, 'sy':syn})
			else:
				tave = (av1*(int(nima/2)+(nima%2)) + av2*int(nima/2))/nima
			# write the current average
			# fil_table=filt_from_fsc_bwt(frsc, low=0.5)
			# tave=filt_table(tave,fil_table)
			dropImage(tave,os.path.join(outdir,"aqm%03d.spi"%iter),"s")
		else:
			break

	for im in xrange(nima):
		temp.read_image(stack,im)
		alpha = data[im].get_attr('alpha')
		sx =  data[im].get_attr('sx')
		sy =  data[im].get_attr('sy')
		mn =  data[im].get_attr('mirror')
		temp.set_attr_dict({'alpha':alpha, 'sx':sx, 'sy':sy,'mirror': mn})
		temp.write_image(stack,im)
	#for im in xrange(nima): data[im].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	return	
"""

def eqprojGSq(args, data):
	from projection import prgs
	from utilities import info
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask,
	#  args: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy
	proj = prgs(data[0], data[1], args)
	#v = -proj.cmp("SqEuclidean", data[2], {"mask":shifted_mask})
	#        CURRENTLY THE DISTANCE IS cross-correlation coefficient
	v = -proj.cmp("SqEuclidean", data[2], {"mask":data[3]})
	#v = proj.cmp("ccc", data[2], {"mask":data[3], "negative":0})
	#v = proj.cmp("ccc", data[2], {"mask":shifted_mask, "negative":0})
	#print  " AMOEBA o", args, v
	return v
	
def eqprojGccc(args, data):
	from projection import prgs
	from utilities import info
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask,
	#  args: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy
	proj = prgs(data[0], data[1], args)
	#v = -proj.cmp("SqEuclidean", data[2], {"mask":shifted_mask})
	#        CURRENTLY THE DISTANCE IS cross-correlation coefficient
	#v = -proj.cmp("SqEuclidean", data[2], {"mask":data[3]})
	v = proj.cmp("ccc", data[2], {"mask":data[3], "negative":0})
	#v = proj.cmp("ccc", data[2], {"mask":shifted_mask, "negative":0})
	#print  " AMOEBA o", args, v
	return v


def eqprojL(args, data):
	from projection import project
	#print  " AMOEBA ",args
	#  data: 0 - vol,  1 - radius, 2 - image,  3 - mask,
	#  args: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy
	proj = project(data[0], args, data[1] )
	v = -proj.cmp("SqEuclidean", data[2], {"mask":data[3]})
	#v = proj.cmp("ccc", data[2], {"mask":data[3], "negative":0})
	return v

def oct_test_L_o():
	from random import random
	from time import time
	from math import sqrt
	import os
	from string import replace
	import sys
	from projection import prep_vol, prgs
	from utilities import model_circle, even_angles, model_gauss_noise
	from fundamentals import fpol

	sys.argv = mpi_init(len(sys.argv),sys.argv)
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid = mpi_comm_rank(MPI_COMM_WORLD)
	
	ic = 4
	filename = "result%4d"%(myid)
	filename  = replace(filename, " ", "0")
	outf = open(filename, "w")
	dirname =  "tempdir%4d"%(myid)
	dirname = replace(dirname, " ", "0")

	osr = 1.5

	vol = EMData()
	vol.read_image("R70S_f.spi")
	volft,kb = prep_vol(vol)
	nx = vol.get_xsize()
	ny = vol.get_ysize()
	nz = vol.get_zsize()
	if nx!=ny or ny!=nz : 
		print "Warning: volume is not a cube!"
		exit()
	else                : 
		n = nx
		del nx,ny,nz
	
	mask = model_circle(int(n/2)-4, n, n)

	delta_theta = 10
	angles=even_angles(delta_theta, 0.0, 90.0, 0.0, 359.9, "S", symmetry='c1', phiEqpsi='Minus')
	
	for u in xrange(7):
		snr= 10**(u/2.0-1)
		stack = "R70S%4d.hdf"%(myid)
		stack = replace(stack, " ", "0")
		os.system('rm -f '+stack)

		real_params = []

		for i in xrange(ic):
			dphi = 4.0*(random()-0.5)
			dtheta = 4.0*(random()-0.5)
			dpsi = 4.0*(random()-0.5)	
			ds2x = 2.0*(random()-0.5)
			ds2y = 2.0*(random()-0.5)
			
			pp = myid*ic+i
			
			phi = angles[pp][0]+dphi
			theta = angles[pp][1]+dtheta
			psi = angles[pp][2]+dpsi
			s2x = -2.0+ds2x
			s2y = 3.0+ds2y  
	
			real_params.append([phi, theta, psi, s2x, s2y])
	
			proj = prgs(volft, kb, [phi, theta, psi, s2x, s2y])
			stat = Util.infomask(proj,mask,1)
			noise = model_gauss_noise(stat[1]/sqrt(snr),n,n)
			proj = proj+noise
			proj = fpol(proj, int(n*osr), int(n*osr))
			proj.set_attr_dict({'alpha':0.0, 'sx':0.0, 'sy':0.0, 'phi':angles[pp][0], 'theta':angles[pp][1], 'psi':angles[pp][2], 's2x':-2.0*osr, 's2y':3.0*osr, 'mirror':0, 'active':1, 'ctf_applied':0})
			proj.write_image(stack, i)
	
		start_time = time()
		tt, tt2 = ali3d_e_L(stack, "R70S_fx15.spi", dirname, maskfile=None, radius=-1, dtheta=2, max_it=1, symmetry="c1", CTF=False)
		end_time = time()

		# Calculating Error
		error = 0.0
		error2 = 0.0
		ang_error = 0.0
		ang_error2 = 0.0
		shift_error = 0.0
		shift_error2 = 0.0

		for im in xrange(ic):
			ima = EMData()
			ima.read_image(stack, im)
			phi = ima.get_attr("phi")
			theta = ima.get_attr("theta")
			psi = ima.get_attr("psi")
			s2x = ima.get_attr("s2x")
			s2y = ima.get_attr("s2y")
			mirror = ima.get_attr("mirror")
			
			this_err = max_3D_pixel_error3(phi, theta, psi, s2x/osr, s2y/osr, real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4], n/2)
			this_ang_err = max_3D_pixel_error3(phi, theta, psi, real_params[im][3], real_params[im][4], real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4], n/2)
			this_shift_err = sqrt((s2x/osr-real_params[im][3])**2+(s2y/osr-real_params[im][4])**2)
			#print phi, theta, psi, s2x/osr, s2y/osr, real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4]
			#print "Projection", im+1, "  error =", this_err, "  ang_error =", this_ang_err, "  shift_error =", this_shift_err
			error = error+this_err  
			error2 = error2+this_err**2	
			ang_error = ang_error+this_ang_err	
			ang_error2 = ang_error2+this_ang_err**2 
			shift_error = shift_error+this_shift_err	
			shift_error2 = shift_error2+this_shift_err**2	
	
		datstrings = []
		datstrings.append("%15f %15f %15f %15f %15f %15f %15f %15f\n" %(error,error2,ang_error,ang_error2,shift_error,shift_error2,tt,tt2))  
		outf.write("".join(datstrings)) 
	outf.close()

def oct_test_L():
	from random import random
	from time import time
	from math import sqrt
	import os
	from string import replace
	import sys
	from projection import prep_vol, prgs
	from utilities import model_circle, even_angles, model_gauss_noise
	from fundamentals import fpol

	sys.argv = mpi_init(len(sys.argv),sys.argv)
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid = mpi_comm_rank(MPI_COMM_WORLD)
	
	ic = 4
	filename = "result%4d"%(myid)
	filename  = replace(filename, " ", "0")
	outf = open(filename, "w")
	dirname =  "tempdir%4d"%(myid)
	dirname = replace(dirname, " ", "0")

	vol = EMData()
	vol.read_image("R70S_f.spi")
	volft,kb = prep_vol(vol)
	nx = vol.get_xsize()
	ny = vol.get_ysize()
	nz = vol.get_zsize()
	if nx!=ny or ny!=nz : 
		print "Warning: volume is not a cube!"
		exit()
	else                : 
		n = nx
		del nx,ny,nz
	
	mask = model_circle(int(n/2)-4, n, n)

	delta_theta = 10
	angles=even_angles(delta_theta, 0.0, 90.0, 0.0, 359.9, "S", symmetry='c1', phiEqpsi='Minus')
	
	for u in xrange(7):
		snr= 10**(u/2.0-1)
		stack = "R70S%4d.hdf"%(myid)
		stack = replace(stack, " ", "0")
		os.system('rm -f '+stack)

		real_params = []

		for i in xrange(ic):
			dphi = 4.0*(random()-0.5)
			dtheta = 4.0*(random()-0.5)
			dpsi = 4.0*(random()-0.5)	
			ds2x = 2.0*(random()-0.5)
			ds2y = 2.0*(random()-0.5)
			
			pp = myid*ic+i
			
			phi = angles[pp][0]+dphi
			theta = angles[pp][1]+dtheta
			psi = angles[pp][2]+dpsi
			s2x = -2.0+ds2x
			s2y = 3.0+ds2y  
	
			real_params.append([phi, theta, psi, s2x, s2y])
	
			proj = prgs(volft, kb, [phi, theta, psi, s2x, s2y])
			stat = Util.infomask(proj,mask,1)
			noise = model_gauss_noise(stat[1]/sqrt(snr),n,n)
			proj = proj+noise
			proj.set_attr_dict({'alpha':0.0, 'sx':0.0, 'sy':0.0, 'phi':angles[pp][0], 'theta':angles[pp][1], 'psi':angles[pp][2], 's2x':-2.0, 's2y':3.0, 'mirror':0, 'active':1, 'ctf_applied':0})
			proj.write_image(stack, i)
	
		start_time = time()
		tt, tt2 = ali3d_e_L(stack, "R70S_f.spi", dirname, maskfile=None, radius=-1, dtheta=2, max_it=1, symmetry="c1", CTF=False)
		end_time = time()

		# Calculating Error
		error = 0.0
		error2 = 0.0
		ang_error = 0.0
		ang_error2 = 0.0
		shift_error = 0.0
		shift_error2 = 0.0

		for im in xrange(ic):
			ima = EMData()
			ima.read_image(stack, im)
			phi = ima.get_attr("phi")
			theta = ima.get_attr("theta")
			psi = ima.get_attr("psi")
			s2x = ima.get_attr("s2x")
			s2y = ima.get_attr("s2y")
			mirror = ima.get_attr("mirror")
			
			this_err = max_3D_pixel_error3(phi, theta, psi, s2x, s2y, real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4], n/2)
			this_ang_err = max_3D_pixel_error3(phi, theta, psi, real_params[im][3], real_params[im][4], real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4], n/2)
			this_shift_err = sqrt((s2x-real_params[im][3])**2+(s2y-real_params[im][4])**2)
			#print phi, theta, psi, s2x/osr, s2y/osr, real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4]
			#print "Projection", im+1, "  error =", this_err, "  ang_error =", this_ang_err, "  shift_error =", this_shift_err
			error = error+this_err  
			error2 = error2+this_err**2	
			ang_error = ang_error+this_ang_err	
			ang_error2 = ang_error2+this_ang_err**2 
			shift_error = shift_error+this_shift_err	
			shift_error2 = shift_error2+this_shift_err**2	
	
		datstrings = []
		datstrings.append("%15f %15f %15f %15f %15f %15f %15f %15f\n" %(error,error2,ang_error,ang_error2,shift_error,shift_error2,tt,tt2))  
		outf.write("".join(datstrings)) 
	outf.close()

def oct_test_G():
	from random import random
	from time import time
	from math import sqrt
	import os
	from string import replace
	import sys
	from projection import prep_vol, prgs
	from utilities import model_circle, even_angles, model_gauss_noise
	from fundamentals import fpol

	sys.argv = mpi_init(len(sys.argv),sys.argv)
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid = mpi_comm_rank(MPI_COMM_WORLD)
	
	option = 1
	ic = 4
	filename = "result%4d"%(myid)
	filename  = replace(filename, " ", "0")
	outf = open(filename, "w")
	dirname =  "tempdir%4d"%(myid)
	dirname = replace(dirname, " ", "0")

	vol = EMData()
	vol.read_image("R70S_f.spi")
	volft,kb = prep_vol(vol)
	nx = vol.get_xsize()
	ny = vol.get_ysize()
	nz = vol.get_zsize()
	if nx!=ny or ny!=nz : 
		print "Warning: volume is not a cube!"
		exit()
	else                : 
		n = nx
		del nx,ny,nz
	
	mask = model_circle(int(n/2)-4, n, n)

	delta_theta = 10
	angles=even_angles(delta_theta, 0.0, 90.0, 0.0, 359.9, "S", symmetry='c1', phiEqpsi='Minus')
	
	for u in xrange(7):
		snr= 10**(u/2.0-1)
		stack = "R70S%4d.hdf"%(myid)
		stack = replace(stack, " ", "0")
		os.system('rm -f '+stack)

		real_params = []

		for i in xrange(ic):
			dphi = 4.0*(random()-0.5)
			dtheta = 4.0*(random()-0.5)
			dpsi = 4.0*(random()-0.5)	
			ds2x = 2.0*(random()-0.5)
			ds2y = 2.0*(random()-0.5)
			
			pp = myid*ic+i
			
			phi = angles[pp][0]+dphi
			theta = angles[pp][1]+dtheta
			psi = angles[pp][2]+dpsi
			s2x = -2.0+ds2x
			s2y = 3.0+ds2y  
	
			real_params.append([phi, theta, psi, s2x, s2y])
	
			proj = prgs(volft, kb, [phi, theta, psi, s2x, s2y])
			stat = Util.infomask(proj,mask,1)
			noise = model_gauss_noise(stat[1]/sqrt(snr),n,n)
			proj = proj+noise
			proj.set_attr_dict({'alpha':0.0, 'sx':0.0, 'sy':0.0, 'phi':angles[pp][0], 'theta':angles[pp][1], 'psi':angles[pp][2], 's2x':-2.0, 's2y':3.0, 'mirror':0, 'active':1, 'ctf_applied':0})
			proj.write_image(stack, i)
	
		start_time = time()
		if option==1:
			tt, tt2 = ali3d_e_G(stack, "R70S_f.spi", "tempdirG6", maskfile=None, radius=-1, dtheta=2, max_it=1, symmetry="c1", CTF=False, Way="SqEuclidean")
		elif option==2:
			tt, tt2 = ali3d_e_G(stack, "R70S_f.spi", "tempdirG7", maskfile=None, radius=-1, dtheta=2, max_it=1, symmetry="c1", CTF=False, Way="ccc")
		elif option==3:
			tt, tt2 = ali3d_e_G2(stack, "R70S_f.spi", "tempdirG8", maskfile=None, radius=-1, dtheta=2, max_it=1, symmetry="c1", CTF=False)
		elif option==4:
			tt, tt2 = ali3d_e_G3(stack, "R70S_f.spi", "tempdirG9", maskfile=None, radius=-1, dtheta=2, max_it=1, symmetry="c1", CTF=False)
		elif option==5:
			tt, tt2 = ali3d_e_G4(stack, "R70S_f.spi", "tempdirG10", maskfile=None, radius=-1, dtheta=2, max_it=1, symmetry="c1", CTF=False)
		else:
			print "Unknown option!"	
		end_time = time()

		# Calculating Error
		error = 0.0
		error2 = 0.0
		ang_error = 0.0
		ang_error2 = 0.0
		shift_error = 0.0
		shift_error2 = 0.0

		for im in xrange(ic):
			ima = EMData()
			ima.read_image(stack, im)
			phi = ima.get_attr("phi")
			theta = ima.get_attr("theta")
			psi = ima.get_attr("psi")
			s2x = ima.get_attr("s2x")
			s2y = ima.get_attr("s2y")
			mirror = ima.get_attr("mirror")
			
			this_err = max_3D_pixel_error3(phi, theta, psi, s2x, s2y, real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4], n/2)
			this_ang_err = max_3D_pixel_error3(phi, theta, psi, real_params[im][3], real_params[im][4], real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4], n/2)
			this_shift_err = sqrt((s2x-real_params[im][3])**2+(s2y-real_params[im][4])**2)
			#print phi, theta, psi, s2x/osr, s2y/osr, real_params[im][0], real_params[im][1], real_params[im][2], real_params[im][3], real_params[im][4]
			#print "Projection", im+1, "  error =", this_err, "  ang_error =", this_ang_err, "  shift_error =", this_shift_err
			error = error+this_err  
			error2 = error2+this_err**2	
			ang_error = ang_error+this_ang_err	
			ang_error2 = ang_error2+this_ang_err**2 
			shift_error = shift_error+this_shift_err	
			shift_error2 = shift_error2+this_shift_err**2	
	
		datstrings = []
		datstrings.append("%15f %15f %15f %15f %15f %15f %15f %15f\n" %(error,error2,ang_error,ang_error2,shift_error,shift_error2,tt,tt2))  
		outf.write("".join(datstrings)) 
	outf.close()


def ali3d_e_G(stack, ref_vol, outdir, maskfile, radius=-1, snr=1.0, dtheta=2, max_it=10, symmetry="c1", CTF = False, Way="SqEuclidean"):
	"""
	An experimental version of ali3d_e		
	"""
	from alignment	import eqproj, Numrinit, ringwe, Applyws
	from filter     import filt_ctf, filt_params, filt_table, filt_from_fsc
	from fundamentals   import fshift, fft
	from projection import prep_vol
	from utilities  import amoeba, model_circle, get_arb_params, set_arb_params, dropSpiderDoc
	from utilities  import dropImage, amoeba2
	from math       import pi, sin, sqrt
	from string     import replace
	from reconstruction import recons3d_4nn, recons3d_4nn_ctf
	from statistics import fsc
	import os 
	import sys
	from sys import exit
	from time import time

	nima = EMUtil.get_image_count(stack)

	vol = EMData()
	vol.read_image(ref_vol)
	nx  = vol.get_xsize()
	if radius <= 0:  radius = nx//2-1
	if os.path.exists(outdir):  os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	vol.write_image(os.path.join(outdir,"ref_volf00.hdf"))
	
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask3D=getImage(maskfile)
		else: mask3D = maskfile
	else:
		mask3D = model_circle(radius, nx, nx, nx)
	mask2D = model_circle(radius, nx, nx)
	dataim = []
	parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
	for im in xrange(nima):
		ima = EMData()
		ima.read_image(stack, im)
		if(CTF):
			ctf_params = get_arb_params(ima, parnames)
			if(ctf_params[6] == 0):
				from filter import filt_ctf
				if(im==0): print  " APPLYING CTF"
				ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
				set_arb_params(ima, ctf_params, parnames)  #I am not sure whether this is needed
		dataim.append(ima)
	
	par_str=["phi", "theta", "psi", "s2x", "s2y"]
	total_time = 0.0
	total_time2 = 0.0
	for iteration in xrange(max_it):
		Util.mul_img(vol, mask3D)
		volft,kb  = prep_vol(vol)
		data = [0]*4
		data[0] = volft
		data[1] = kb
		data[3] = mask2D
		#step = 0
		for imn in xrange(nima):
			begin_time = time()
			#print "Projection", imn
		
			data[2] = dataim[imn]
			atparams = get_arb_params(dataim[imn], par_str)
			#  change signs of shifts for projections
			#atparams[3] *= -1
			#atparams[4] *= -1
			weight_phi = max(dtheta, dtheta*abs((atparams[1]-90.0)/180.0*pi))
			
			# For downhill simplex method			
			if Way=="SqEuclidean":
				optm_params =  amoeba(atparams, [weight_phi,dtheta,weight_phi,1.0,1.0], eqprojGSq, 1.e-5,1.e-5,500,data)
			elif Way=="ccc":
				optm_params =  amoeba(atparams, [weight_phi,dtheta,weight_phi,1.0,1.0], eqprojGccc, 1.e-5,1.e-5,500,data)
			else: 
				print "Wrong Way!"
			optm_params[0].append(imn)
			set_arb_params(dataim[imn], [optm_params[0][0], optm_params[0][1], optm_params[0][2], optm_params[0][3], optm_params[0][4]], par_str)
			
			# For LBFGSB method
			#optm_params = Util.twoD_to_3D_ali(volft,kb,dataim[imn],mask2D,atparams[0],atparams[1],atparams[2],atparams[3],atparams[4])
			#set_arb_params(dataim[imn], [optm_params[0], optm_params[1], optm_params[2], optm_params[3], optm_params[4]], par_str)
			
			#optm_params[0][3] *= -1
			#optm_params[0][4] *= -1
			#print "Projection", imn, "  ", optm_params[2], "steps"
			#step += optm_params[2]
			end_time = time()
			total_time += (end_time-begin_time)
			total_time2 += (end_time-begin_time)**2
		#print "Average step = ", step/float(nima)
		
			
		for im in xrange(nima):
			dataim[im].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	return total_time, total_time2

def eqprojG2(args, data):
	from fundamentals import fft
	from sys import exit
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask,
	#  args: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy
	
	# proj = prgs(data[0], data[1], args)
	volft = data[0]
	kb = data[1]
	params = args
	
	# This part is copied from prgs
	EULER_SPIDER = Transform3D.EulerType.SPIDER
	psi = params[2]
	theta = params[1]
	phi = params[0]
	R= Transform3D(EULER_SPIDER,phi,theta,psi)
	temp = volft.extractplane(R,kb)
	temp.fft_shuffle()
	temp.center_origin_fft()

	if(params[3]!=0. or params[4]!=0.):
		params = {"filter_type" : Processor.fourier_filter_types.SHIFT, "x_shift" : params[3], "y_shift" : params[4], "z_shift" : 0.0}
		temp=Processor.EMFourierFilter(temp, params)
	
	v = -temp.cmp("SqEuclidean", data[4])
	return v


def ali3d_e_G2(stack, ref_vol, outdir, maskfile, radius=-1, snr=1.0, dtheta=2, max_it=10, symmetry="c1", CTF = False):
	"""
	An experimental version of ali3d_e		
	"""
	from alignment	import eqproj, Numrinit, ringwe, Applyws
	from filter     import filt_ctf, filt_params, filt_table, filt_from_fsc
	from fundamentals   import fshift, fft
	from projection import prep_vol
	from utilities  import amoeba, model_circle, get_arb_params, set_arb_params, dropSpiderDoc
	from utilities  import dropImage, amoeba2
	from math       import pi,sin
	from string     import replace
	from reconstruction import recons3d_4nn, recons3d_4nn_ctf
	from statistics import fsc
	import os 
	import sys
	from sys import exit
	from time import time

	nima = EMUtil.get_image_count(stack)

	vol = EMData()
	vol.read_image(ref_vol)
	nx  = vol.get_xsize()
	if radius <= 0:  radius = nx//2-1
	if os.path.exists(outdir):  os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	vol.write_image(os.path.join(outdir,"ref_volf00.hdf"))
	
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask3D=getImage(maskfile)
		else: mask3D = maskfile
	else:
		mask3D = model_circle(radius, nx, nx, nx)
	mask2D = model_circle(radius, nx, nx)
	dataim = []
	parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
	for im in xrange(nima):
		ima = EMData()
		ima.read_image(stack, im)
		if(CTF):
			ctf_params = get_arb_params(ima, parnames)
			if(ctf_params[6] == 0):
				from filter import filt_ctf
				if(im==0): print  " APPLYING CTF"
				ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
				set_arb_params(ima, ctf_params, parnames)  #I am not sure whether this is needed
		dataim.append(ima)
	
	par_str=["phi", "theta", "psi", "s2x", "s2y"]
	total_time = 0.0
	total_time2 = 0.0
	for iteration in xrange(max_it):
		Util.mul_img(vol, mask3D)
		volft,kb  = prep_vol(vol)
		data = [0]*5
		data[0] = volft
		data[1] = kb
		data[3] = mask2D
		#new_params = []
		#step = 0
		for imn in xrange(nima):
			begin_time = time()
			#print "Projection", imn
	
			data[2] = dataim[imn].copy()
			refi = dataim[mn].norm_pad(False, 2)
			refi.do_fft_inplace()
			data[4] = refi.copy()
			
			atparams = get_arb_params(dataim[imn], par_str)
			#  change signs of shifts for projections
			#atparams[3] *= -1
			#atparams[4] *= -1
			weight_phi = max(dtheta, dtheta*abs((atparams[1]-90.0)/180.0*pi))			
			
			# For downhill simplex method 
			optm_params =  amoeba(atparams, [weight_phi,dtheta,weight_phi,1.0,1.0], eqprojG2, 1.e-5,1.e-5,500,data)
			optm_params[0].append(imn)
			#optm_params[0][3] *= -1
			#optm_params[0][4] *= -1
			set_arb_params(dataim[imn], [optm_params[0][0], optm_params[0][1], optm_params[0][2], optm_params[0][3], optm_params[0][4]], par_str)
			
			# For LBFGSB method
			# optm_params = Util.twoD_to_3D_ali(volft,kb,dataim[imn],mask2D,atparams[0],atparams[1],atparams[2],atparams[3],atparams[4])
			# set_arb_params(dataim[imn], [optm_params[0], optm_params[1], optm_params[2], optm_params[3], optm_params[4]], par_str)
			#step += optm_params[2]
			#print "Projection", imn, "  ", optm_params[2], "steps"
			end_time = time()
			total_time += (end_time-begin_time)
			total_time2 += (end_time-begin_time)**2
		#print "Average step = ", step/float(nima)
		for im in xrange(nima):
			dataim[im].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	return total_time, total_time2
			
def twoD_fine_search(args, data):
	return data[0].get_pixel_conv7(args[0]*2, args[1]*2, 0.0, data[1])

def eqprojG3(args, data):
	from utilities import amoeba
	from fundamentals import ccf
	from development import twoD_fine_search
	#from sys import exit
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask,
	#  args: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy
	
	# proj = prgs(data[0], data[1], args)
	#volft = data[0]
	#kb = data[1]
	#kb2 = data[6]
	#params = args
	
	# This part is copied from prgs
	EULER_SPIDER = Transform3D.EulerType.SPIDER
	R    = Transform3D(EULER_SPIDER, args[0], args[1], args[2])
	temp = data[0].extractplane(R, data[1])
	M    = temp.get_ysize()	
	"""
	temp.fft_shuffle()
	temp = temp.Four_ds(M/2, M/2, 1, False)
	temp.center_origin_fft()
	temp = temp.FourInterpol_i(M, M, 1, False)
	"""
	temp = temp.Four_shuf_ds_cen_us(M, M, 1, False)

	nx = M/2
	sx = (nx-data[7][0]*2)/2.0
	sy = (nx-data[7][1]*2)/2.0

	data2 = []
	data2.append( ccf(temp, data[5]) )
	data2.append(data[6])
	#  search for shift
	ps = amoeba( [sx,sy], [0.05,0.05], twoD_fine_search, 1.e-5,1.e-5, 500, data2)
	
	s2x = (nx-ps[0][0]*2)/2
	s2y = (nx-ps[0][1]*2)/2
	
	params2 = {"filter_type" : Processor.fourier_filter_types.SHIFT, "x_shift" : s2x*2, "y_shift" : s2y*2, "z_shift" : 0.0}
	temp2 = Processor.EMFourierFilter(temp, params2)
	v = -temp2.cmp("SqEuclidean", data[4])
	
	#J = -temp.cmp("dot",temp)
	#v2 = ps[1]*2/256.0/256.0-(J+data[6])
	#print J, data[6], ps[1]*2/256.0/256.0, v, v2
	
	return v, [s2x, s2y]

def prepij(image):
	M=image.get_ysize()
	npad = 2
	N = M*npad
	K = 6
	alpha = 1.75
	r = M/2
	v = K/2.0/N
	kb = Util.KaiserBessel(alpha, K, r, v, N)
	params = {"filter_type": Processor.fourier_filter_types.KAISER_SINH_INVERSE, "alpha":alpha, "K":K, "r":r, "v":v, "N":N}
	o = image.FourInterpol(2*M, 2*M, 1, 0)
	q = Processor.EMFourierFilter(o, params)
	return  o, q, kb
	
def ali3d_e_G3(stack, ref_vol, outdir, maskfile, radius=-1, snr=1.0, dtheta=2, max_it=10, symmetry="c1", CTF = False):
	"""
	An experimental version of ali3d_e		
	"""
	from alignment	import eqproj, Numrinit, ringwe, Applyws
	from filter     import filt_ctf, filt_params, filt_table, filt_from_fsc
	from fundamentals   import fshift, fft
	from projection import prep_vol
	from utilities  import amoeba, model_circle, get_arb_params, set_arb_params, dropSpiderDoc
	from utilities  import dropImage, amoeba2, model_blank, info, pad
	from math       import pi,sin
	from string     import replace
	from reconstruction import recons3d_4nn, recons3d_4nn_ctf
	from statistics import fsc
	import os 
	import sys
	from sys import exit
	from time import time

	nima = EMUtil.get_image_count(stack)

	vol = EMData()
	vol.read_image(ref_vol)
	nx  = vol.get_xsize()
	if radius <= 0:  radius = nx//2-1
	if os.path.exists(outdir):  os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	vol.write_image(os.path.join(outdir,"ref_volf00.hdf"))
	
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask3D=getImage(maskfile)
		else: mask3D = maskfile
	else:
		mask3D = model_circle(radius, nx, nx, nx)
	mask2D = model_circle(radius, nx, nx)
	dataim = []
	parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
	for im in xrange(nima):
		ima = EMData()
		ima.read_image(stack, im)
		if(CTF):
			ctf_params = get_arb_params(ima, parnames)
			if(ctf_params[6] == 0):
				from filter import filt_ctf
				if(im==0): print  " APPLYING CTF"
				ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
				set_arb_params(ima, ctf_params, parnames)  #I am not sure whether this is needed
		dataim.append(ima)
	
	par_str=["phi", "theta", "psi", "s2x", "s2y"]
	total_time = 0.0
	total_time2 = 0.0
	for iteration in xrange(max_it):
		Util.mul_img(vol, mask3D)
		volft,kb  = prep_vol(vol)
		data = [0]*8
		data[0] = volft
		data[1] = kb
		data[3] = mask2D
		#new_params = []
		#step = 0 
		for imn in xrange(nima):
			begin_time = time()
			#print "Projection", imn
	
			data[2] = dataim[imn].copy()
			
			refi = dataim[imn].copy()
			#refi2 = pad(refi,nx*2,nx*2)
			oo, qq, kb2 = prepij(refi)
			data[4] = oo
			data[5] = qq
			data[6] = kb2 
			
			#refi.divkbsinh(kb)
			#refi = refi.FourInterpol(M*2, M*2, 1, 0)
			#refi = Processor.EMFourierFilter(refi, params)
			#refi = refi.pad_fft(2)
			#refi.center_padded()
			#refi.do_fft_inplace()
			#data[4] = refi.copy()
			
			#refi = dataim[imn].copy()
			#refi = refi.pad_fft(2)
			#refi.center_padded()
			#refi.do_fft_inplace()
			#data[6] = refi.copy()
			
			#data[4] = data[2].FourInterpol(nx*2, nx*2, 1, 0)
			#F = -data[4].cmp("dot",data[4])
			
			atparams = get_arb_params(dataim[imn], par_str)
			data[7] = [atparams[3], atparams[4]]
			#data[6] = F
			del atparams[3]
			del atparams[3]
			weight_phi = max(dtheta, dtheta*abs((atparams[1]-90.0)/180.0*pi))			
			
			# For downhill simplex method 
			optm_params =  amoeba2(atparams, [weight_phi,dtheta,weight_phi], eqprojG3, 1.e-5,1.e-5,500,data)
			set_arb_params(dataim[imn], [optm_params[0][0], optm_params[0][1], optm_params[0][2], optm_params[3][0], optm_params[3][1]], par_str)
			#step += optm_params[2]
			#print "Projection", imn, "  ", optm_params[2], "steps"
			end_time = time()
			total_time += (end_time-begin_time)
			total_time2 += (end_time-begin_time)**2
		#print "Average step = ", step/float(nima)
		for im in xrange(nima):
			dataim[im].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	return total_time, total_time2

def ali_G3(data, atparams, delta):
	from utilities import amoeba2
	from development import prepij
	oo, qq, kb2 = prepij(data[2])
	data.insert(4, oo)
	data.insert(5, qq)
	data.insert(6, kb2)
	data.insert(7, [-atparams[3], -atparams[4]])

	weight_phi = max(delta, delta*abs((atparams[1]-90.0)/180.0*pi))	
	optm_params =  amoeba2(atparams, [weight_phi, delta, weight_phi], eqprojG3, 1.e-5,1.e-5,500,data)

	del data[4]
	del data[4]
	del data[4]
	del data[4]

	return optm_params

def eqprojG4(args, data):
	from utilities import peak_search, amoeba, dropImage, info
	from fundamentals import fft, ccf, fpol
	from sys import exit
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask,
	#  args: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy
	
	# proj = prgs(data[0], data[1], args)
	volft = data[0]
	kb = data[1]
	params = args
	
	# This part is copied from prgs
	EULER_SPIDER = Transform3D.EulerType.SPIDER
	psi = params[2]
	theta = params[1]
	phi = params[0]
	R= Transform3D(EULER_SPIDER,phi,theta,psi)
	temp = volft.extractplane(R,kb)
	temp.fft_shuffle()
	temp.center_origin_fft()
	temp.do_ift_inplace()
	M = temp.get_ysize()/2
	temp = temp.window_center(M)
	
	nx = temp.get_ysize()
	sx = (nx-data[5][0]*2)/2
	sy = (nx-data[5][1]*2)/2
	
	aaa = fpol(temp, 2*M, 2*M)
	product = ccf(aaa, data[4])

	"""
	npad = 2
	N = M*npad
	K = 6
	alpha = 1.75
	r = M/2
	v = K/2.0/N
	#kb = Util.KaiserBessel(alpha, K, r, v, N)
	params = {"filter_type": Processor.fourier_filter_types.KAISER_SINH_INVERSE, "alpha":alpha, "K":K, "r":r, "v":v, "N":N}
	q = Processor.EMFourierFilter(product, params)	
	"""
	data2 = [0]*2
	data2[0] = product
	data2[1] = kb
	ps = amoeba([sx,sy],[1.0,1.0],twoD_fine_search,1.e-5,1.e-5,500,data2)
	
	s2x = nx/2-ps[0][0]
	s2y = nx/2-ps[0][1]
	params2 = {"filter_type" : Processor.fourier_filter_types.SHIFT, "x_shift" : s2x, "y_shift" : s2y, "z_shift" : 0.0}
	temp2 = Processor.EMFourierFilter(temp, params2)
	v = -temp2.cmp("SqEuclidean", data[2])
	
	return v, [s2x, s2y]


def ali3d_e_G4(stack, ref_vol, outdir, maskfile, radius=-1, snr=1.0, dtheta=2, max_it=10, symmetry="c1", CTF = False):
	"""
	An experimental version of ali3d_e		
	"""
	from alignment	import eqproj, Numrinit, ringwe, Applyws
	from filter     import filt_ctf, filt_params, filt_table, filt_from_fsc
	from fundamentals   import fshift, fft
	from projection import prep_vol
	from utilities  import amoeba, model_circle, get_arb_params, set_arb_params, dropSpiderDoc
	from utilities  import dropImage, amoeba2, model_blank, info
	from math       import pi,sin
	from string     import replace
	from reconstruction import recons3d_4nn, recons3d_4nn_ctf
	from statistics import fsc
	import os 
	import sys
	from sys import exit
	from time import time

	nima = EMUtil.get_image_count(stack)

	vol = EMData()
	vol.read_image(ref_vol)
	nx  = vol.get_xsize()
	if radius <= 0:  radius = nx//2-1
	if os.path.exists(outdir):  os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	vol.write_image(os.path.join(outdir,"ref_volf00.hdf"))
	
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask3D=getImage(maskfile)
		else: mask3D = maskfile
	else:
		mask3D = model_circle(radius, nx, nx, nx)
	mask2D = model_circle(radius, nx, nx)
	dataim = []
	parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
	for im in xrange(nima):
		ima = EMData()
		ima.read_image(stack, im)
		if(CTF):
			ctf_params = get_arb_params(ima, parnames)
			if(ctf_params[6] == 0):
				from filter import filt_ctf
				if(im==0): print  " APPLYING CTF"
				ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
				set_arb_params(ima, ctf_params, parnames)  #I am not sure whether this is needed
		dataim.append(ima)
	
	M = nx
	npad = 2
	N = M*npad
	K = 6
	alpha = 1.75
	r = M/2
	v = K/2.0/N
	#kb = Util.KaiserBessel(alpha, K, r, v, N)
	params = {"filter_type": Processor.fourier_filter_types.KAISER_SINH_INVERSE, "alpha":alpha, "K":K, "r":r, "v":v, "N":N}
	
	
	par_str=["phi", "theta", "psi", "s2x", "s2y"]
	total_time = 0.0
	total_time2 = 0.0
	for iteration in xrange(max_it):
		Util.mul_img(vol, mask3D)
		volft,kb  = prep_vol(vol)
		data = [0]*6
		data[0] = volft
		data[1] = kb
		data[3] = mask2D
		#new_params = []
		#step = 0 
		for imn in xrange(nima):
			begin_time = time()
			#print "Projection", imn
	
			data[2] = dataim[imn].copy()

			refi = dataim[imn].copy()
			refi = refi.FourInterpol(nx*2,nx*2,0,True)
			data[4] = Processor.EMFourierFilter(refi, params)
			
			atparams = get_arb_params(dataim[imn], par_str)
			data[5] = [atparams[3], atparams[4]]
			del atparams[3]
			del atparams[3]
			weight_phi = max(dtheta, dtheta*abs((atparams[1]-90.0)/180.0*pi))			
			
			# For downhill simplex method 
			optm_params =  amoeba2(atparams, [weight_phi,dtheta,weight_phi], eqprojG4, 1.e-5,1.e-5,500,data)
			set_arb_params(dataim[imn], [optm_params[0][0], optm_params[0][1], optm_params[0][2], optm_params[3][0], optm_params[3][1]], par_str)
			#step += optm_params[2]
			#print "Projection", imn, "  ", optm_params[2], "steps"
			end_time = time()
			total_time += (end_time-begin_time)
			total_time2 += (end_time-begin_time)**2
		#print "Average step = ", step/float(nima)
		for im in xrange(nima):
			dataim[im].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	return total_time, total_time2

			
def ali3d_e_L(stack, ref_vol, outdir, maskfile, radius=-1, snr=1.0, dtheta=2, max_it=10, symmetry="c1", CTF = False):
	"""
	A temporary replacement of ali3d_e		
	"""
	from alignment	import Numrinit, ringwe, Applyws
	from filter     import filt_ctf, filt_params, filt_table, filt_from_fsc
	from fundamentals   import fshift, fft
	from projection import prep_vol
	from utilities  import amoeba, model_circle, get_arb_params, set_arb_params, dropSpiderDoc
	from utilities  import dropImage, amoeba2
	from math       import pi,sin
	from string     import replace
	from reconstruction import recons3d_4nn, recons3d_4nn_ctf
	from statistics import fsc
	import os 
	import sys
	from time import time

	nima = EMUtil.get_image_count(stack)

	vol = EMData()
	vol.read_image(ref_vol)
	nx  = vol.get_xsize()
	if radius <= 0:  radius = nx//2-1
	if os.path.exists(outdir):  os.system('rm -rf '+outdir)
	os.mkdir(outdir)
	vol.write_image(os.path.join(outdir,"ref_volf00.hdf"))
	
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):  mask3D=getImage(maskfile)
		else: mask3D = maskfile
	else:
		mask3D = model_circle(radius, nx, nx, nx)
	mask2D = model_circle(radius, nx, nx)
	dataim = []
	parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
	for im in xrange(nima):
		ima = EMData()
		ima.read_image(stack, im)
		if(CTF):
			ctf_params = get_arb_params(ima, parnames)
			if(ctf_params[6] == 0):
				from filter import filt_ctf
				if(im==0): print  " APPLYING CTF"
				ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
				set_arb_params(ima, ctf_params, parnames)  #I am not sure whether this is needed
		dataim.append(ima)
	

	par_str=["phi", "theta", "psi", "s2x", "s2y"]
	total_time = 0.0
	total_time2 = 0.0
	for iteration in xrange(max_it):
		Util.mul_img(vol, mask3D)
		data = []
		data.insert(0, vol)
		data.insert(1, radius)
		data.insert(3, mask2D)
		#new_params = []
		#step = 0
		for imn in xrange(nima):
			begin_time = time()
			#print iteration, imn
			data.insert(2, dataim[imn])
			
			atparams = get_arb_params(dataim[imn], par_str)
			#  change signs of shifts for projections
			#atparams[3] *= -1
			#atparams[4] *= -1
			#initial  = eqproj(atparams, data)  # this is if we need initial discrepancy
			
			#stheta   = abs(sin(atparams[1]*pi/180.0))
			#if stheta > 0.0: weight_phi=min(180.0,dtheta/stheta/2.0)
			#else           : weight_phi=180.0
			weight_phi = max(dtheta, dtheta*abs((atparams[1]-90.0)/180.0*pi))			
			optm_params =  amoeba(atparams, [weight_phi,dtheta,weight_phi,1.0,1.0], eqprojL, 1.e-5,1.e-5,500,data)
			
			optm_params[0].append(imn)
			#optm_params[0][3] *= -1
			#optm_params[0][4] *= -1
			#new_params.append(optm_params[0])
			del  data[2]
			set_arb_params(dataim[imn], [optm_params[0][0], optm_params[0][1], optm_params[0][2], optm_params[0][3], optm_params[0][4]], par_str)
			end_time = time()
			total_time += (end_time-begin_time) 
			total_time2 += (end_time-begin_time)**2
			#step += optm_params[2]
			#print "Projection", imn, "  ", optm_params[2], "steps"
		#print "Average step = ", step/float(nima)
		"""
		#  3D stuff
		list_p = range(0,nima,2)
		if(CTF): vol1 = recons3d_4nn_ctf(stack, list_p, snr, 1, symmetry)
		else:	 vol1 = recons3d_4nn(stack, list_p, symmetry)

		list_p = range(1,nima,2)
		if(CTF): vol2 = recons3d_4nn_ctf(stack, list_p, snr, 1, symmetry)
		else:	 vol2 = recons3d_4nn(stack, list_p, symmetry)

		[mean, sigma, xmin, xmax ] =  Util.infomask(vol1, mask3D, False)
		vol1 -= mean
		Util.mul_img(vol1, mask3D)
		[mean, sigma, xmin, xmax ] =  Util.infomask(vol2, mask3D, False)
		vol2 -= mean
		Util.mul_img(vol2, mask3D)
		
		filename = replace("fsc%3d"%(iteration+1)," ","0")
		res = fsc(vol1, vol2, 1.0, os.path.join(outdir, filename))
		del vol1
		del vol2

		# calculate new and improved 3D
		list_p = range(nima)
		if(CTF): vol = recons3d_4nn_ctf(stack, list_p, snr, 1, symmetry)
		else:	 vol = recons3d_4nn(stack, list_p, symmetry)
		# store the reference volume
		filename =  replace("vol%3d.spi"%(iteration+1)," ","0")
		dropImage(vol,os.path.join(outdir, filename), "s")
		# lk = 0
		# while(fscc[1][lk] >0.9 and fscc[0][lk]<0.25):	lk+=1
		# fl = fscc[0][lk]
		# fh = min(fl+0.1,0.49)
		# vol = filt_btwl(vol, fl, fh)
		cs   = vol.phase_cog()
		vol  = fshift(vol, -cs[0], -cs[1] -cs[2])
		filename = replace("volf%3d.spi"%(iteration+1)," ","0")
		dropImage(vol,os.path.join(outdir, filename), "s")
		"""
		
		for im in xrange(nima):
			dataim[im].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	return total_time, total_time2

def max_3D_pixel_error1(phi1, theta1, psi1, sx1, sy1, phi2, theta2, psi2, sx2, sy2, r):
	from numpy import mat, linalg
	from math import cos, sin, sqrt, pi

	phi1 = phi1/180.0*pi
	theta1 = theta1/180.0*pi
	psi1 = psi1/180.0*pi
	phi2 = phi2/180.0*pi
	theta2 = theta2/180.0*pi
	psi2 = psi2/180.0*pi	
	R1a = mat([[cos(phi1), sin(phi1), 0],[-sin(phi1), cos(phi1), 0],[0, 0, 1]])
	R1b = mat([[cos(theta1), 0, -sin(theta1)],[0, 1, 0],[sin(theta1), 0, cos(theta1)]])
	R1c = mat([[cos(psi1), sin(psi1), 0],[-sin(psi1), cos(psi1), 0],[0, 0, 1]])
	R1  = R1a*R1b*R1c	
	R1inv = linalg.inv(R1) 
	R2a = mat([[cos(phi2), sin(phi2), 0],[-sin(phi2), cos(phi2), 0],[0, 0, 1]])
	R2b = mat([[cos(theta2), 0, -sin(theta2)],[0, 1, 0],[sin(theta2), 0, cos(theta2)]])
	R2c = mat([[cos(psi2), sin(psi2), 0],[-sin(psi2), cos(psi2), 0],[0, 0, 1]])
	R2  = R2a*R2b*R2c
	s1  = mat([[sx1],[sy1],[0]])
	s2  = mat([[sx2],[sy2],[0]])
	dmax = 0
	for i in range(-r,r+1):
		for j in range(-r,r+1):
			for k in range(-r,r+1):
				dis = sqrt(i*i+j*j+k*k)
				if (r-dis >= 0) and (r-dis <= 1):
					X = mat([[i],[j],[k]])
					d = R1inv*(R2*X+s2-s1)-X
					dd = sqrt(d[0,0]*d[0,0]+d[1,0]*d[1,0]+d[2,0]*d[2,0])
					if dd > dmax: 
						dmax=dd
	return dmax

def max_3D_pixel_error2(phi1, theta1, psi1, sx1, sy1, phi2, theta2, psi2, sx2, sy2, r):
	from numpy import mat, linalg
	from math import cos, sin, sqrt, pi
	from utilities import even_angles

	phi1 = phi1/180.0*pi
	theta1 = theta1/180.0*pi
	psi1 = psi1/180.0*pi
	phi2 = phi2/180.0*pi
	theta2 = theta2/180.0*pi
	psi2 = psi2/180.0*pi	
	R1a = mat([[cos(phi1), sin(phi1), 0],[-sin(phi1), cos(phi1), 0],[0, 0, 1]])
	R1b = mat([[cos(theta1), 0, -sin(theta1)],[0, 1, 0],[sin(theta1), 0, cos(theta1)]])
	R1c = mat([[cos(psi1), sin(psi1), 0],[-sin(psi1), cos(psi1), 0],[0, 0, 1]])
	R1  = R1a*R1b*R1c	
	R1inv = linalg.inv(R1) 
	R2a = mat([[cos(phi2), sin(phi2), 0],[-sin(phi2), cos(phi2), 0],[0, 0, 1]])
	R2b = mat([[cos(theta2), 0, -sin(theta2)],[0, 1, 0],[sin(theta2), 0, cos(theta2)]])
	R2c = mat([[cos(psi2), sin(psi2), 0],[-sin(psi2), cos(psi2), 0],[0, 0, 1]])
	R2  = R2a*R2b*R2c
	s1  = mat([[sx1],[sy1],[0]])
	s2  = mat([[sx2],[sy2],[0]])
	dmax = 0
	angles = even_angles(0.5, 0.0, 180.0, 0.0, 359.9, "S", symmetry='c1', phiEqpsi='Minus')
	nangles = len(angles)
	for i in range(nangles):
		X = mat([[r*sin(angles[i][1]*pi/180.0)*cos(angles[i][0]*pi/180.0)],[r*sin(angles[i][1]*pi/180.0)*sin(angles[i][0]*pi/180.0)],[r*cos(angles[i][1]*pi/180.0)]])
		d = R1inv*(R2*X+s2-s1)-X
		dd = sqrt(d[0,0]*d[0,0]+d[1,0]*d[1,0]+d[2,0]*d[2,0])
		if dd > dmax: 	
			dmax=dd
	return dmax

"""	
def max_3D_pixel_error3(phi1, theta1, psi1, sx1, sy1, phi2, theta2, psi2, sx2, sy2, r):
	from numpy import mat, linalg, concatenate, eye
	from math import cos, sin, sqrt, pi
	from utilities import even_angles

	phi1 = phi1/180.0*pi
	theta1 = theta1/180.0*pi
	psi1 = psi1/180.0*pi
	phi2 = phi2/180.0*pi
	theta2 = theta2/180.0*pi
	psi2 = psi2/180.0*pi	
	R1a = mat([[cos(phi1), sin(phi1), 0],[-sin(phi1), cos(phi1), 0],[0, 0, 1]])
	R1b = mat([[cos(theta1), 0, -sin(theta1)],[0, 1, 0],[sin(theta1), 0, cos(theta1)]])
	R1c = mat([[cos(psi1), sin(psi1), 0],[-sin(psi1), cos(psi1), 0],[0, 0, 1]])
	R1  = R1a*R1b*R1c
	R1e = concatenate((concatenate((R1,[[sx1],[sy1],[0]]),1), [[0,0,0,1]]))
	R1inv = linalg.inv(R1e) 
	R2a = mat([[cos(phi2), sin(phi2), 0],[-sin(phi2), cos(phi2), 0],[0, 0, 1]])
	R2b = mat([[cos(theta2), 0, -sin(theta2)],[0, 1, 0],[sin(theta2), 0, cos(theta2)]])
	R2c = mat([[cos(psi2), sin(psi2), 0],[-sin(psi2), cos(psi2), 0],[0, 0, 1]])
	R2  = R2a*R2b*R2c
	R2e = concatenate((concatenate((R2,[[sx2],[sy2],[0]]),1), [[0,0,0,1]]))
	dmax = 0
	angles = even_angles(0.5, 0.0, 180.0, 0.0, 359.9, "S", symmetry='c1', phiEqpsi='Minus')
	nangles = len(angles)
	for i in range(nangles):
		X = mat([[r*sin(angles[i][1]*pi/180.0)*cos(angles[i][0]*pi/180.0)],[r*sin(angles[i][1]*pi/180.0)*sin(angles[i][0]*pi/180.0)],[r*cos(angles[i][1]*pi/180.0)], [1.0]])
		d = (R1inv*R2e-eye(4))*X
		dd = sqrt(d[0,0]*d[0,0]+d[1,0]*d[1,0]+d[2,0]*d[2,0])
		if dd > dmax: 	
			dmax=dd
	return dmax
"""

def max_3D_pixel_error3(phi1, theta1, psi1, sx1, sy1, phi2, theta2, psi2, sx2, sy2, r):
	from numpy import mat, linalg, concatenate, eye
	from math import cos, sin, sqrt, pi
	from utilities import even_angles

	phi1 = phi1/180.0*pi
	theta1 = theta1/180.0*pi
	psi1 = psi1/180.0*pi
	phi2 = phi2/180.0*pi
	theta2 = theta2/180.0*pi
	psi2 = psi2/180.0*pi	
	R1a = mat([[cos(phi1), sin(phi1), 0],[-sin(phi1), cos(phi1), 0],[0, 0, 1]])
	R1b = mat([[cos(theta1), 0, -sin(theta1)],[0, 1, 0],[sin(theta1), 0, cos(theta1)]])
	R1c = mat([[cos(psi1), sin(psi1), 0],[-sin(psi1), cos(psi1), 0],[0, 0, 1]])
	R1  = R1a*R1b*R1c
	R1e = concatenate((concatenate((R1,[[sx1],[sy1],[0]]),1), [[0,0,0,1]]))
	R1inv = linalg.inv(R1e) 
	R2a = mat([[cos(phi2), sin(phi2), 0],[-sin(phi2), cos(phi2), 0],[0, 0, 1]])
	R2b = mat([[cos(theta2), 0, -sin(theta2)],[0, 1, 0],[sin(theta2), 0, cos(theta2)]])
	R2c = mat([[cos(psi2), sin(psi2), 0],[-sin(psi2), cos(psi2), 0],[0, 0, 1]])
	R2  = R2a*R2b*R2c
	R2e = concatenate((concatenate((R2,[[sx2],[sy2],[0]]),1), [[0,0,0,1]]))
	L = R1inv*R2e-eye(4)
	dmax = 0
	angles = even_angles(1.0, 0.0, 180.0, 0.0, 359.9, "S", symmetry='c1', phiEqpsi='Minus')
	nangles = len(angles)
	for i in range(nangles):
		rad0 = angles[i][0]*pi/180.0
		rad1 = angles[i][1]*pi/180.0
		X = mat([[r*sin(rad1)*cos(rad0)],[r*sin(rad1)*sin(rad0)],[r*cos(rad1)], [1.0]])
		d = L*X
		dd = d[0,0]*d[0,0]+d[1,0]*d[1,0]+d[2,0]*d[2,0]
		if dd > dmax: 	
			dmax=dd
	return sqrt(dmax)
	

def ali_with_mask(vol, mdl, mask):
	vol_mask = vol*mask
	mdl_mask = mdl*mask

	vol_cs = vol_mask.phase_cog()
	mdl_cs = mdl_mask.phase_cog()

	vol_mask = fshift(vol, -vol_cs[0], -vol_cs[1], -vol_cs[2])
	mdl_mask = fshift(mdl, -mdl_cs[0], -mdl_cs[1], -mdl_cs[2])
	trans = ali_vol_3(vol_mask, mdl_mask, 2.0, 1.0)
	newvol = fshift(vol, -vol_cs[0], -vol_cs[1], -vol_cs[2])
	newvol = rot_shift3D(newvol, trans[0], trans[1], trans[2], trans[3], trans[4], trans[5], 1.0)
	newvol = fshift(vol,  mdl_cs[0],  mdl_cs[1],  mdl_cs[2])
	return newvol

#def ali_vol_rotation(vol, refv, radius=None):
def rot_3D_add_n(vol, refv, phi=0, theta=0, psi=0, radius=None):
	# rotation only
	from alignment    import ali_vol_func
	from utilities    import get_im, model_circle, model_blank, get_arb_params, set_arb_params, dropImage
	from utilities    import amoeba
	from fundamentals import rot_shift3D
	ang_scale=5.0
	ref = get_im(refv)
	nx = ref.get_xsize()
	ny = ref.get_ysize()
	nz = ref.get_zsize()
	if(radius != None):    mask = model_circle(radius, nx, ny, nz)
	else:                  mask = model_circle(float(min(nx, ny, nz)//2-2), nx, ny, nz)

	names_params = ["phi", "theta", "psi"]
	params = get_arb_params(ref, names_params)
	ref = rot_shift3D(ref, params[0], params[1], params[2])

	e = get_im(vol)
	params = get_arb_params(ref, names_params)
	print  params
	scale = [ang_scale, ang_scale, ang_scale]
	data=[e, ref, mask]
	params = amoeba(params, scale, ali_vol_func, 1.e-4, 1.e-4,500, data)
	print  params
	set_arb_params(e, params, names_params)
	e.write_image(stack, n,  EMUtil.ImageType.IMAGE_HDF, True)

def rot_3D_add_n(stack, outdir, phi=0, theta=0, psi=0, radius=None):
	
	from alignment import find_rotation
	from utilities import get_im, model_circle, model_blank, get_arb_params, set_arb_params, dropImage
	from fundamentals import rot_shift3D
	import sys
	import os

	N = EMUtil.get_image_count(stack)

	ref = get_im(stack, 0)
	nx = ref.get_xsize()
	ny = ref.get_ysize()
	nz = ref.get_zsize()
	if(radius != None):
		mask = model_circle(radius, nx, ny, nz)
	else:
		mask = model_circle(float(min(nx, ny, nz)//2-2), nx, ny, nz)

	names_params = ["phi", "theta", "psi", "s3x", "s3y", "s3z"]
	params = get_arb_params(ref, names_params)
	ref = rot_shift3D(ref, params[0], params[1], params[2], params[3], params[4], params[5])

	for n in xrange(1,N):
		e = get_im(stack, n)
		params = get_arb_params(ref, names_params)
		print  n,params
		params = find_rotation(e, ref, mask, params)
		e = rot_shift3D(e, params[0], params[1], params[2], params[3], params[4], params[5])
		Util.add_img(ref, e)
		print  n,params
		set_arb_params(e, params, names_params)
		e.write_image(stack, n,  EMUtil.ImageType.IMAGE_HDF, True)
	Criter = ref.cmp("dot", ref, {"negative":0, "mask":mask})
	

	angle_change = True
	cnt=0
	while(angle_change):
		print "Iteration: ",cnt,Criter
		nref = model_blank(nx, ny, nz)
		for n in xrange(N):
			e = get_im(stack, n)
			params = get_arb_params(ref, names_params)
			temp = rot_shift3D(e, params[0], params[1], params[2], params[3], params[4], params[5])
			Util.sub_img(ref, temp)
			Util.add_img(nref, temp)
			params = find_rotation(e, ref, mask, params)
			e = rot_shift3D(e, params[0], params[1], params[2], params[3], params[4], params[5])
			Util.add_img(ref, e)
			set_arb_params(e, params, names_params)
			e.write_image(stack, n,  EMUtil.ImageType.IMAGE_HDF, True)
		cnt += 1
		newt = nref.cmp("dot", nref, {"negative":0, "mask":mask})
		if(newt <= Criter):  angle_change = False
		Criter = newt
		ref = nref.copy()

	dropImage(ref,outdir+"/vols.spi")



def pufit(infile, Pixel_size):
	""" 
		Taken from morphology
		Fit power spectrum model from 
		Power spectrum of the structure 
		created by X-ray crystallography
	"""
	from utilities  	import getImage, amoeba, readSpiderDoc, get_im
	from math               import log
	from fundamentals 	import rops
	#from numpy 		import exp
	#from scipy.optimize 	import fmin,leastsq, fmin
	#from optparse 		import OptionParser
	#from scipy 		import arange
	#from numpy 		import log
	#from sparx 		import TFList
	fpw2         = rops(get_im(infile))
	nr           = fpw2.get_xsize()
	fpw = []
	frq = []
	for i in xrange(1,nr):
		frq.append(i/float(2*nr)/Pixel_size)
		fpw.append(fpw2.get_value_at(i))
	scale = fpw[0]
	norm = fpw[1]
	nr = len(fpw)
	for i in xrange(nr):	fpw[i] /= norm
	flo = []
	for i in xrange(nr):	flo.append(log(fpw[i]))
	data = []
	data.insert(0,flo)
	data.insert(1,frq)
	params = [-10.0, 10.0, 0.05]
	ooo = amoeba(params, [0.1, 1.0, 0.001], residuals_simplex, 1.e-4, 1.e-4, 500, data)
	print ooo
	for i in xrange(1,nr):  print  frq[i], flo[i], ooo[0][0] + ooo[0][1]/(data[1][i]/ooo[0][2]+1.0)**2
	return  ooo[0]
	'''
	# fit Gaussian like peaks 
	#  Fitting the peak around 1/10 Angstrom
	if 2.*Pixel_size+1. < 10.:
		xpeak_1   = 1./(5.) # 7
		xpeak_2   = 1./(11.)  # 16
		ix_1      = int(xpeak_1/step)
		ix_2      = int(xpeak_2/step)
		freq_carb = .1
		sig_carb  = sgm1**2
		p1        = [y_true[ix_1], freq_carb, sig_carb]
		print '%10.3g %10.3g'%(ix_1,ix_2)
		y1        = y_true[ix_2:ix_1]
		x1        = x[ix_2:ix_1]
		print plsq[0]
		plsq     = leastsq(residuals_lsq_peak,p1,(y1,x1,c0))
		d1,d2,d3 = plsq[0]
		c1,c2,c3 = c0
		for i in xrange(len(pw2)):	pw2[i]=exp(c1)*exp(c2/(x[i]+c3)**2)+d1*exp(-(x[i]-d2)**2/d3)
       # fitting the peak around 1/5 Angstrom
		if (2.*Pixel_size + 1. < 5.):
			xpeak_1   = 1./(2.*Pixel_size+1.)
			xpeak_2   = 1./(6.)
			ix_1      = int(xpeak_1/step)
			ix_2      = int(xpeak_2/step)
			freq_carb = .2
			sig_carb  = sgm2**2
			p1        = [y_true[ix_1],freq_carb,sig_carb]
			y1        = y_true[ix_2:ix_1]
			x1        = x[ix_2:ix_1]
			plsq      = leastsq(residuals_lsq_peak,p1,(y1,x1,c0))
			p1        = plsq[0]
			plsq      = leastsq(residuals_lsq_peak,p1,(y1,x1,c0))
			h1,h2,h3  = plsq[0]
			c1,c2,c3  = c0
			for i in xrange(len(pw2)):	pw2[i] = exp(c1)*exp(c2/(x[i] + c3)**2)+d1*exp(-(x[i]-d2)**2/d3) + h1*exp(-(x[i]-h2)**2/h3)
	else: # Fitting those power spectrum whose nyquist frequency less than 1/10 Angstrom 
		pw2 = exp(c1)*exp(c2/(x+c3)**2)
	out = TFList(nrows,3)
	for i in xrange(1,nrows+1):
		out.SetVal(i,2,y_true[i-1]/y_scale)
		out.SetVal(i,1,x[i-1])
		out.SetVal(i,2,pw2[i-1]/y_scale)	
	out.write(outfile)
	'''


def extract_signal_from_1dpw2_cl1(indir, outdir, Pixel_size = 1, polynomial_rankB = 2, cut_off = 0):
	"""
		Extract signal from 1D rotationally averaged 
		power spectra saved in a directory 
	"""
	import os
	from morphorlogy import residual_1dpw2
	flist = os.listdir(outdir)
	if os.path.exists(indir)  is False: os.mkdir(outdir)
	for i, single_file in xrange(len(flist)):
		(filename, filextension) = os.path.splitext(single_file)
		input_file    = os.path.join(indir, single_file)
		pw = readSpiderDoc(input_file)
		out_file     = os.path.join(outdir, "residual_of_" + filename + ".txt")
		res = residual_1dpw2(list_1dpw2, polynomial_rankB, Pixel_size, cut_off)
		dropSpiderDoc(out_file, res)



"##################   WHAT FOLLOWS ARE VARIOUS ALIGNMENT PROCEDURES     #####################"


def oned_search_func(args,data):
	#print  " AMOEBA i",args
	v = data[0].get_pixel_conv7(args[0]*2, 0, 0, data[1])
	#print  " AMOEBA o",args,v
	return v
	
def oned_search_func_new(args,data0,data1):
	#print  " AMOEBA i",args
	v = -data0.get_pixel_conv7(args*2, 0, 0, data1)
	#print  " AMOEBA o",args,v
	return v
	
def apmq(image, crefim, xrng, yrng, step, mode, numr, cnx, cny):
	"""Determine shift and rotation between image and many reference images (crefim, weights have to be applied)
		quadratic interpolation
	"""
	from math import pi, cos, sin
	#from utilities import ttime#,info
	#print "APMQ"
	#print  ttime()
	#cimage=Util.Polar2Dm(image, cnx, cny, numr, mode)
	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	for i in xrange(-ky, ky+1):
		iy = i*step
		for  j in xrange(-kx, kx+1):
			ix = j*step
			cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
			#for l in xrange(20000):   cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
			#print  "Polar2Dm ",ttime()
			Util.Frngs(cimage, numr)
			#for l in xrange(20000):   retvals = Util.Crosrng_ms(cimage, cimage, numr)
			#print  "Crosrng_ms ",ttime()
			#from sys import exit
			#exit()
			#imref = retvals["qn"]
			#for l in xrange(6000):   Util.Frngs(cimage, numr)
			#print  "Frngs    ",ttime()
			#  compare with all reference images
			for iref in xrange(len(crefim)):
				retvals = Util.Crosrng_ms(crefim[iref], cimage, numr)
				#print  retvals
				#from sys import exit
				#exit()
				#for l in xrange(6000):  retvals = Util.Crosrng_ms(crefim[iref], cimage, numr)
				#print  "Crosrng  ",ttime()
				qn = retvals["qn"]
				qm = retvals["qm"]
				if(qn >=peak or qm >=peak):
					sx = -ix
					sy = -iy
					nref = iref
					if (qn >= qm):
						ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
						peak=qn
						mirror=0
					else:
						ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
						peak=qm
						mirror=1
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang, sxs, sys, mirror, peak, nref

def diff_projdir(n1, phi2, theta2):
	from math import cos, sin, pi
	qv = pi/180.
	#n1 = [ sin(theta1*qv)*cos(phi1) ,  sin(theta1*qv)*sin(phi1*qv) , cos(theta1*qv)]
	n2 = [ sin(theta2*qv)*cos(phi2*qv) ,  sin(theta2*qv)*sin(phi2*qv) , cos(theta2*qv)]
	#return acos(abs(n1[0]*n2[0] + n1[1]*n2[1] + n1[2]*n2[2]))*180.0/pi
	return abs(n1[0]*n2[0] + n1[1]*n2[1] + n1[2]*n2[2])
	
def apmq_local(image, crefim, xrng, yrng, step, ant, mode, numr, cnx, cny):
	"""Determine shift and rotation between image and many reference images (crefim, weights have to be applied)
		quadratic interpolation
	"""
	from math import pi, cos, sin
	from alignment import diff_projdir
	#from utilities import ttime#,info
	#print "APMQ"
	#print  ttime()
	#cimage=Util.Polar2Dm(image, cnx, cny, numr, mode)
	phi,theta,psi,s2x,s2y = get_params_proj( image )
	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	for i in xrange(-ky, ky+1):
		iy = i*step
		for  j in xrange(-kx, kx+1):
			ix = j*step
			cimage = Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
			#for l in xrange(20000):   cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
			#print  "Polar2Dm ",ttime()
			Util.Frngs(cimage, numr)
			#for l in xrange(20000):   retvals = Util.Crosrng_ms(cimage, cimage, numr)
			#print  "Crosrng_ms ",ttime()
			#from sys import exit
			#exit()
			#imref = retvals["qn"]
			#for l in xrange(6000):   Util.Frngs(cimage, numr)
			#print  "Frngs    ",ttime()
			#  compare with all reference images
			for iref in xrange(len(crefim)):
				n1 = []
				n1.append(crefim[iref].get_attr('n1'))
				n1.append(crefim[iref].get_attr('n2'))
				n1.append(crefim[iref].get_attr('n3'))
				if(diff_projdir(n1, phi, theta) >= ant):
					retvals = Util.Crosrng_ms(crefim[iref], cimage, numr)
					#print  retvals
					#from sys import exit
					#exit()
					#for l in xrange(6000):  retvals = Util.Crosrng_ms(crefim[iref], cimage, numr)
					#print  "Crosrng  ",ttime()
					qn = retvals["qn"]
					qm = retvals["qm"]
					if(qn >=peak or qm >=peak):
						sx = -ix
						sy = -iy
						nref = iref
						if (qn >= qm):
							ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
							peak=qn
							mirror=0
						else:
							ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
							peak=qm
							mirror=1
	if(peak == -1.0E23):
		ang = 0; sxs = 0; sys = 0; mirror = 0;
		nref = -1
	else:
		co =  cos(ang*pi/180.0)
		so = -sin(ang*pi/180.0)
		sxs = sx*co - sy*so
		sys = sx*so + sy*co
	return  ang, sxs, sys, mirror, peak, nref

def apmqs(image, refim, first_ring, last_ring, rstep, xrng, yrng, step, mode = "F"):
	"""Determine shift and rotation between images and many reference images (refim)
		quadratic interpolation
	"""
	from utilities import model_circle
	#from utilities import info, ttime
	#print "ORMQ"
	#print  ttime()
	mode = "F"
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr = ringwe(numr, mode)
	crefim = []
	nx=refim[0].get_xsize()
	ny=refim[0].get_ysize()
	mask = model_circle(last_ring, nx, ny)
	cnx = int(nx/2)+1
	cny = int(ny/2)+1
	for j in xrange(len(refim)):
		cimage = Util.Polar2Dm(refim[j].process_inplace("normalize.mask", {"mask":mask, "no_sigma":1}), cnx, cny, numr, mode)
		#cimage = Util.Polar2Dm(refim[j], cnx, cny, numr, mode)
		Util.Frngs(cimage, numr)
		Applyws(cimage, numr, wr)
		crefim.append(cimage)

	outparams = []
	for im in xrange(len(image)):	
		outparams.append(apmq(image[im], crefim, xrng, yrng, step, mode, numr, cnx, cny))
	return  outparams
	
def apnq(image, crefim, xrng, yrng, step, mode, numr, cnx, cny):
	"""Determine shift and rotation between image and many reference images (crefim, weights have to be applied)
		quadratic interpolation
		no MIRROR
	"""
	from math import pi, cos, sin
	#print "APNQ"
	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	for i in xrange(-ky, ky+1):
		iy = i*step
		for  j in xrange(-kx, kx+1):
			ix = j*step
			cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
			Util.Frngs(cimage, numr)
			#  compare with all reference images
			for iref in xrange(len(crefim)):
				retvals = Util.Crosrng_e(crefim[iref], cimage, numr, 0)
				qn = retvals["qn"]
				if(qn >= peak):
					sx = -ix
					sy = -iy
					nref = iref
					ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
					peak=qn
	mirror=0
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang, sxs, sys, mirror, peak, nref

def apply_trans2d(data, kb):
	"""
		Apply alignment parameters
	"""
	from fundamentals import rotshift2dg
	n = len(data)
	nx = data[0].get_xsize()
	ny = data[0].get_ysize()
	dala = []
	for i in xrange(n):
		alpha  = data[i].get_attr('alpha')
		sx     = data[i].get_attr('sx')
		sy     = data[i].get_attr('sy')
		mirror = data[i].get_attr('mirror')
		temp = rotshift2dg(data[i], alpha, sx, sy, kb)
		if  mirror: temp.process_inplace("mirror",{"axis":'x'})
		dala.append(temp)
	return dala


def aptrans(image, params):
	""""
	  apply spider style transformation parameters to an image
	"""
	from fundamentals import rtshg
	output = rtshg(image, params[0], params[1], params[2])
	if params[3]: output.process_inplace("mirror", {"axis":'x'})
	return  output


	
def combine_params_new(spider_trans,ref_ali_params):
	""""
	  combine spider style transformation doc file (alpha,sx,sy,mirrory)
	  with the results of ref_ali (phi,theta,psi,nsx,nsy)
	  Output:
		angles: in spider style (psi,theta,phi)
	"""
	angles=[]
	new_trans=[]
	for i in xrange(0,len(ref_ali_params)/5):
		angles.append([ref_ali_params[i*5],ref_ali_params[i*5+1],ref_ali_params[i*5+2]])
		if(spider_trans[i*4+3]==0):
			#no mirror, simply add shifts
			new_trans.append([spider_trans[i*4],spider_trans[i*4+1]+ref_ali_params[i*5+2],spider_trans[i*4+2]+ref_ali_params[i*5+3],spider_trans[i*4+3]])
		else:
			#mirror, subtract shifts
			new_trans.append([spider_trans[i*4],spider_trans[i*4+1]-ref_ali_params[i*5+2],spider_trans[i*4+2]-ref_ali_params[i*5+3],spider_trans[i*4+3]])
	return  angles,new_trans

def dfunc(args,data):
	from math import pi
	#print  " AMOEBA ",args
	# gridding rotation, arguments: angle, sx, sy, kb
	res = data[0].rot_scale_conv7(args[0]*pi/180., args[1], args[2], data[2], 1.0)
	#v = res.cmp("ccc", data[1], {"mask":data[3], "negative":0})
	v = -res.cmp("SqEuclidean", data[1], {"mask":data[3]})
	#print  " AMOEBA o",args,v
	return v

def dfunc2(args,data):
	# rotation arguments: angle, sx, sy, scale
	res = data[0].rot_scale_trans2D(args[0], args[1], args[2], 1.0)
	#v = res.cmp("ccc", data[1], {"mask":data[2], "negative":0})
	v = -res.cmp("SqEuclidean", data[1], {"mask":data[2]})
	#print  " AMOEBA o",args,v
	return v

def dfunc_i(args,data):
	from math import pi
	res = data[0].rot_scale_conv7(args[0]*pi/180., args[1], args[2], data[2], 1.0)
	v = res.cmp("SqEuclidean", data[1], {"mask":data[3]})
	return v

def dfunc2_i(args,data):
	res = data[0].rot_scale_trans2D(args[0], args[1], args[2], 1.0)
	v = res.cmp("SqEuclidean", data[1], {"mask":data[2]})
	return v
		
def stack_variance(stack, maskfile, flip):
	from utilities import model_blank
	from fundamentals import fft

	if flip==0: maskfile = 1.0 - maskfile
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	ima = fft(ima)
	nx = ima.get_xsize()
	ny = ima.get_ysize()
	ima_ave = model_blank(nx/2,ny)	
	ima_ave = ima_ave.real2complex()
	ima_ave2 = model_blank(nx/2,ny)
	for i in xrange(nima):
		ima.read_image(stack,i)
		Util.mul_img(ima,maskfile)
		ima = fft(ima)
		Util.add_img(ima_ave, ima)
		ima = ima.absi()
		Util.add_img2(ima_ave2, ima)
	ima_ave = ima_ave.absi()
	Util.mul_img(ima_ave,ima_ave)
	Util.mul_scalar(ima_ave,1.0/nima)
	Util.sub_img(ima_ave2,ima_ave)
	Util.mul_scalar(ima_ave2,1.0/(nima-1))
	return ima_ave2

"""	
# This fucntion is added just to compare with the previous one to see if the results
# are the same and the runtime. My results shows that the previous one is one time
# faster than this one.
def stack_variance2(stack, maskfile, flip):
	from utilities import model_blank
	from fundamentals import fft, absi

	if flip==0:
		maskfile = 1-maskfile
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	ima = fft(ima)
	nx = ima.get_xsize()
	ny = ima.get_ysize()
	ima_ave = model_blank(nx/2,ny)
	ima_ave = ima_ave.real2complex()
	ima_ave2 = model_blank(nx/2,ny)
	for i in xrange(nima):
		ima.read_image(stack,i)
		ima = ima*maskfile
		ima = fft(ima)
		ima_ave  = ima_ave+ima
		ima_ave2 = ima_ave2+absi(ima*ima)
	ima_ave  = ima_ave*(ima_ave/nima)
	ima_ave = absi(ima_ave)
	ima_ave2 = ima_ave2-ima_ave
	ima_ave2 = ima_ave2/(nima-1)
	return ima_ave2

def stack_variance3(stack):
	from utilities import model_blank

	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	nx = ima.get_xsize()
	ny = ima.get_ysize()
	ima_ave = model_blank(nx,ny)
	for i in xrange(nima):
		ima.read_image(stack,i)
		ima_ave += ima
		#Util.add_img(ima_ave, ima)
	return ima_ave


def stack_variance3(stack, maskfile, flip):
	from utilities import model_blank
	from fundamentals import fft, absi

	if flip==0:
		maskfile = 1-maskfile
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	ima = fft(ima)
	nx = ima.get_xsize()
	ny = ima.get_ysize()
	ima_ave = model_blank(nx/2,ny)
	ima_ave = ima_ave.real2complex()
	for i in xrange(nima):
		ima.read_image(stack,i)
		ima *= maskfile
		ima=fft(ima)
		ima_ave  += ima
	ima_ave  /= nima
	ima_ave2 = model_blank(nx/2,ny)
	for i in xrange(nima):
		ima.read_image(stack,i)
		ima *= maskfile
		ima = fft(ima)
		ima_ave2 += (absi(ima-ima_ave)*absi(ima-ima_ave))
	ima_ave2 /= (nima-1)
	return ima_ave2
"""

# This function evaluates the alignment error of a stack of images,
# Here para is the theoretical alignment paramenters, D is the diameter of the image
def stack_ali_err(stack, para, D):
	from utilities import inverse_transform2, compose_transform2
	from math import sin, sqrt, pi
	
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	min_err = 1E23
	for i in xrange(nima):
		err = 0.0
		ima.read_image(stack,i)
		angi = ima.get_attr('alpha')
		sxi = ima.get_attr('sx')
		syi = ima.get_attr('sy')
		for j in xrange(nima):
			ima.read_image(stack,j)
			angj = ima.get_attr('alpha')
			sxj = ima.get_attr('sx')
			syj = ima.get_attr('sy')
			alpha1, sx1, sy1, scale1 = inverse_transform2(para[j][0], para[j][1], para[j][2], 1.0)
			alpha2, sx2, sy2, scale2 = compose_transform2(alpha1, sx1, sy1, scale1, para[i][0], para[i][1], para[i][2], 1.0)
			alpha3, sx3, sy3, scale3 = compose_transform2(alpha2, sx2, sy2, scale2, angi, sxi, syi, 1.0)
			alpha_err = abs(alpha3-angj) % 360.0
			sx_err = abs(sx3-sxj)
			sy_err = abs(sy3-syj)
			this_err = D*abs(sin(alpha_err/2.0/180.0*pi))+sqrt(sx_err**2+sy_err**2)
			err = err+this_err
		err /= (nima-1)
		if err < min_err:
			min_err = err
	return min_err
	
	
def stack_ali_err2(stack, para, D):
	from utilities import inverse_transform2, compose_transform2
	from math import sin, sqrt, pi
	
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	for j in xrange(nima):
		ima.read_image(stack,j)
		angj = ima.get_attr('alpha')
		sxj = ima.get_attr('sx')
		syj = ima.get_attr('sy')
		alpha1, sx1, sy1, scale1 = inverse_transform2(para[j][0], para[j][1], para[j][2], 1.0)
		alpha2, sx2, sy2, scale2 = compose_transform2(alpha1, sx1, sy1, scale1, para[i][0], para[i][1], para[i][2], 1.0)
		alpha3, sx3, sy3, scale3 = compose_transform2(alpha2, sx2, sy2, scale2, angi, sxi, syi, 1.0)
		alpha_err = abs(alpha3-angj) % 360.0
		sx_err = abs(sx3-sxj)
		sy_err = abs(sy3-syj)
		this_err = D*abs(sin(alpha_err/2.0/180.0*pi))+sqrt(sx_err**2+sy_err**2)
		err = err+this_err
	err /= (nima-1)
	return min_err

def alifunc(args, data):
	from utilities import model_blank, model_circle
	from fundamentals import rot_shift2D
	from statistics import fsc

	stack = data[0]
	n = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	nx = ima.get_xsize()
	ny = ima.get_ysize()
	ave = model_blank(nx,ny)
	b = model_blank(nx,ny)
	mask = model_circle(int(nx/2)-4,nx,ny)
	for i in xrange(n):
		if i>0:
			ima = EMData()
			ima.read_image(stack,i)
		alpha  =  args[i*3]
		sx     =  args[i*3+1]
		sy     =  args[i*3+2]
		mirror =  ima.get_attr('mirror')
		temp = rot_shift2D(ima,alpha, sx, sy, mirror)
		ave = ave + temp		
	v = ave.cmp("SqEuclidean", b, {"mask":mask})
	print v
	return v
	
"""
	stack = data[0]
	n = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	nx = ima.get_xsize()
	ny = ima.get_ysize()
	ave1 = model_blank(nx,ny)
	ave2 = model_blank(nx,ny)
	for i in xrange(n):
		if i>0:
			ima = EMData()
			ima.read_image(stack,i)
		alpha  =  args[i*3]
		sx     =  args[i*3+1]
		sy     =  args[i*3+2]
		mirror =  ima.get_attr('mirror')
		temp = rot_shift2D(ima,alpha, sx, sy, mirror)
		if((i%2) == 0): Util.add_img(ave1, temp)
		else:          Util.add_img(ave2, temp)
	ave1 /= (n//2+(n%2))
	ave2 /= (n//2)
	frsc = fsc(ave1, ave2, 1.0)
	v = sum(frsc[1])
	print v
	return v
"""

def alifuncg(args, data):
	from utilities import model_blank, model_circle
	from fundamentals import rtshgkb
	from statistics import fsc

	stack = data[0]
	kb = data[1]
	n = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	nx = ima.get_xsize()
	ny = ima.get_ysize()
	ave = model_blank(nx/2,ny/2)
	b = model_blank(nx/2,ny/2)
	mask = model_circle(int(nx/4)-4,nx/2,ny/2)
	for i in xrange(n):
		if i>0:
			ima = EMData()
			ima.read_image(stack,i)
		alpha  =  args[i*3]
		sx     =  args[i*3+1]
		sy     =  args[i*3+2]
		mirror =  ima.get_attr('mirror')
		temp = rtshgkb(ima,alpha,sx,sy,kb)
		if  mirror: temp.process_inplace("mirror", {"axis":'x'})
		ave = ave + temp		
	v = ave.cmp("SqEuclidean", b, {"mask":mask})
	print v
	return v

def eqproj_spin(args, data):
	from projection import prgs
	from math import pi
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask, 
	EULER_SPIN=Transform3D.EulerType.SPIN
	EULER_SPIDER = Transform3D.EulerType.SPIDER
	dict_spin = dict()
	dict_spin["Omega"]=args[0] 
	dict_spin["n1"]=sin(args[1]*pi/180.)*cos(args[2]*pi/180.)
	dict_spin["n2"]=sin(args[1]*pi/180.)*sin(args[2]*pi/180.)
	dict_spin["n3"]=cos(args[1]*pi/180.)
	Rspin=Transform3D(EULER_SPIN,dict_spin)
	vv=Rspin.get_rotation(EULER_SPIDER)
	params=5*[0.0]
	params[0]=vv["phi"]
	params[1]=vv["theta"]
	params[2]=vv["psi"]
	params[3]=args[3]
	params[4]=args[4]

	proj=prgs(data[0], data[1], params)
	v = -proj.cmp("SqEuclidean", data[2], {"mask":data[3]})
	#print  " AMOEBA o",params,v
	return v

def eqproj_(args, data):
	from projection import prgs
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask, 
	proj = prgs(data[0], data[1], args)
	v = -proj.cmp("SqEuclidean", data[2], {"mask":data[3]})
	#print  " AMOEBA o",args,v
	return v

def eqproj_xyx(args,data):
	from projection import prgs
	#print  " AMOEBA ",args
	#  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask, 
	proj=prgs(data[0], data[1], args)
	v = -proj.cmp("SqEuclidean", data[2], {"mask":data[3]})
	#print  " AMOEBA o",args,v
	return v
    

def eqproj2(args, data):
	from projection import prgs
	from fundamentals import fft
	from utilities import amoeba2
	from math import cos, sin, pi
	
	proj = prgs(data[0], data[1], args+[0.0, 0.0, 0.0])
	
	M = data[2].get_xsize()
	sx = data[4][1]
	sy = data[4][2]
	crefim = data[5]
	mode = data[6][0]	
	numr = data[6][1]
	cnx = data[6][2]
	cny = data[6][3]
	kb = data[6][4]
	params = data[6][5]
	maxrin = data[6][6]
	kbline = data[6][7]
	parline = data[6][8]
	
	imali=proj.FourInterpol(2*M,2*M,1,0)
	q=Processor.EMFourierFilter(imali,params)
	imali=fft(q)
	
	is_mirror = 0
		
	data0 = []
	data0.insert(0,imali)
	data0.insert(1,cnx)
	data0.insert(2,cny)
	data0.insert(3,numr)
	data0.insert(4,mode)
	data0.insert(5,kb)
	data0.insert(6,crefim)
	data0.insert(7,parline)
	data0.insert(8,maxrin)
	data0.insert(9,kbline)
	data0.insert(10,is_mirror)
	
	ps2 = amoeba2([sx,sy],[1,1],func_loop2,1.e-4,1.e-4,500,data0)	
		
	sx = -ps2[0][0]
	sy = -ps2[0][1]
	ang = ps2[3]
			
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co

	proj = prgs(data[0], data[1], args+[ang, sxs, sys])
	v = proj.cmp("ccc", data[2], {"mask":data[3], "negative":0})
	return v, [ang, sxs, sys]

def eqproj_xyz(args,data):
    from projection import prgs
    #print  " AMOEBA ",args
    #  data: 0 - volkb,  1 - kb, 2 - image,  3 - mask, 
    EULER_XYZ=Transform3D.EulerType.XYZ
    EULER_SPIDER = Transform3D.EulerType.SPIDER
    dict_xyz = dict()
    dict_xyz["xtilt"]=args[0]
    dict_xyz["ytilt"]=args[1]
    dict_xyz["ztilt"]=args[2]
    Rxyz=Transform3D(EULER_XYZ,dict_xyz)
    vv=Rxyz.get_rotation(EULER_SPIDER)
    params=5*[0.0]
    params[0]=vv["phi"]
    params[1]=vv["theta"]
    params[2]=vv["psi"]
    params[3]=args[3]
    params[4]=args[4]

    proj=prgs(data[0], data[1], params)
    v = -proj.cmp("SqEuclidean", data[2], {"mask":data[3]})
    #print  " AMOEBA o",args,v
    return v

def orm(image, refim, xrng=0, yrng=0, step=1, first_ring=1, last_ring=0, rstep=1, mode = "F"):
	"""  Determine shift and rotation between image and reference image
	     quadratic interpolation
	"""
	nx=refim.get_xsize()
	ny=refim.get_ysize()
	if(last_ring == 0):  last_ring = nx//2-2-max(xrng,yrng)
	# center in SPIDER convention
	cnx = int(nx/2)+1
	cny = int(ny/2)+1
	#precalculate rings
	numr=Numrinit(first_ring, last_ring, rstep, mode)
	wr=ringwe(numr ,mode)
	#for iring in xrange(len(wr)):
	#	print wr[iring], iring
	#cimage=Util.Polar2Dmi(refim, cnx, cny, numr, mode, kb)
	cimage=Util.Polar2Dm(refim, cnx, cny, numr, mode)
	Util.Frngs(cimage, numr)
	Applyws(cimage, numr, wr)
	return ormq(image, cimage, xrng, yrng, step, mode, numr, cnx, cny)
       
def ormqi(image, refim, first_ring, last_ring, rstep=1, xrng=0, yrng=0, step=1, mode="F"):
	"""Determine shift and rotation between image and reference image (refim)
		using gridding resampling
	"""
	from math import pi, cos, sin
	from fundamentals import fft
	#from utilities import info
	#print "ORMQI"
	numr=Numrinit(first_ring, last_ring, rstep, mode)
	wr = ringwe(numr,mode)
	nx = image.get_xsize()
	ny = image.get_ysize()
	cnx = nx/2+1
	cny = ny/2+1

	M=image.get_xsize()
	# padd two times
	npad=2
	N=M*npad
	# support of the window
	K=6
	alpha=1.75
	r=M/2
	v=K/2.0/N
	kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
	oo=refim.FourInterpol(2*M,2*M,1,0)
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	q=Processor.EMFourierFilter(oo,params)
	oo=fft(q)
	crefim=Util.Polar2Dmi(oo, cnx, cny, numr, mode ,kb)
	#info(crefim)
	Util.Frngs(crefim, numr)
	Applyws(crefim, numr, wr)

	oo=image.FourInterpol(2*M,2*M,1,0)
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	q=Processor.EMFourierFilter(oo,params)
	oo=fft(q)
	 
	peak = -1.0E23
	for iy in xrange(-yrng, yrng+1, step):
		for  ix in xrange(-xrng, xrng+1, step):
			cimage=Util.Polar2Dmi(oo, cnx+ix, cny+iy, numr, mode, kb)
			Util.Frngs(cimage, numr)

			#retvals = Util.Crosrng_e(crefim, cimage, numr, 0)
			#print  "  e 0 ",retvals["tot"],retvals["qn"]
			#retvals = Util.Crosrng_e(crefim, cimage, numr, 1)
			#print  "  e 1 ",retvals["tot"],retvals["qn"]
			retvals = Util.Crosrng_ms(crefim, cimage, numr)
			#print  "  ms  ",retvals["tot"],retvals["qn"],retvals["tmt"],retvals["qm"]
			qn = retvals["qn"]
			qm = retvals["qm"]
			if(qn >=peak or qm >=peak):
				sx = -ix
				sy = -iy
				if (qn >= qm):
					ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
					peak=qn
					mirror=0
				else:
					ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
					peak=qm
					mirror=1
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang,sxs,sys,mirror,peak
       
def ormqip(image,crefim,xrng,yrng,step,mode,numr,kb,cnx,cny,nx):
	"""Determine shift and rotation between image (kb prepared) and reference image (crefim)
	"""
	from math import pi,cos,sin
	from fundamentals import fft
	#from utilities import info
	#print "ORMQIP"
	peak = -1.0E23
	for iy in xrange(-yrng,yrng+1,step):
		for  ix in xrange(-xrng,xrng+1,step):
			cimage = Util.Polar2Dmi(image, cnx+ix, cny+iy, numr, mode, kb)
			#cimage=Util.Polar2Dm(image,cnx+ix,cny+iy,numr,mode)
			#info(cimage)
			Util.Frngs(cimage, numr)
			#info(cimage)
			retvals = Util.Crosrng_ms(crefim,cimage,numr)
			#print  retvals["qn"],retvals["tot"],retvals["qm"],retvals["tmt"]
			qn = retvals["qn"]
			qm = retvals["qm"]
			if(qn >=peak or qm >=peak):
				sx = -ix
				sy = -iy
				if (qn >= qm):
					ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
					peak=qn
					mirror=0
				else:
					ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
					peak=qm
					mirror=1
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang,sxs,sys,mirror,peak
       
def ormqg(image,refim,first_ring,last_ring,rstep,xrng,yrng,step,mode):
     """Determine shift and rotation between image and reference image (refim)
     """
     from math import pi
     from fundamentals import fft
     #from utilities import info
     #print "ORMQG"
     numr=Numrinit(first_ring,last_ring,rstep,mode)
     wr = ringwe(numr,mode)
     nx = image.get_xsize()
     ny = image.get_ysize()
     cnx = nx/2+1
     cny = ny/2+1
     
     M=image.get_xsize()
     # padd two times
     npad=2
     N=M*npad
     # support of the window
     K=6
     alpha=1.75
     r=M/2
     v=K/2.0/N
     kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
     oo=refim.FourInterpol(N,N,1,0)
     params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
     q=Processor.EMFourierFilter(oo,params)
     oo=fft(q)
     crefim=Util.Polar2Dmi(oo,cnx,cny,numr,mode,kb)
     #info(crefim)
     Util.Frngs(crefim, numr)
     Applyws(crefim, numr,wr)
     
     oo=image.FourInterpol(2*M,2*M,1,0)
     params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
     q=Processor.EMFourierFilter(oo,params)
     oo=fft(q)
     maxrin=numr[len(numr)-1]
     #print  maxrin
     #  peak_s is a 3D ccf array straight
     peak_s = EMData()
     peak_s.set_size(maxrin,2*xrng+1,2*yrng+1)
     #  peak_m is a 3D ccf array mirrored
     peak_m = EMData()
     peak_m.set_size(maxrin,2*xrng+1,2*yrng+1)
     for iy in xrange(-yrng,yrng+1,step):
       for  ix in xrange(-xrng,xrng+1,step):
	 cimage=Util.Polar2Dmi(oo,cnx+ix,cny+iy,numr,mode,kb)
	 #info(cimage)
	 Util.Frngs(cimage, numr)
	 qt = Util.Crosrng_msg(crefim,cimage,numr)
	 for k in xrange(0,maxrin):
	   peak_s[(k+maxrin/2)%maxrin,ix+xrng,iy+yrng]=qt[k,0]
	   peak_m[(k+maxrin/2)%maxrin,ix+xrng,iy+yrng]=qt[k,1]
     return  peak_s,peak_m

"""
def ormql(image,refim,first_ring,last_ring,rstep,xrng,yrng,step,mode):
	
	#Determine shift and rotation between image and reference image (refim)
	
	from math import pi, cos, sin
	from fundamentals import fft
	from utilities import amoeba, model_circle
	#print "ORMQL"
	numr=Numrinit(first_ring,last_ring,rstep,mode)
	wr = ringwe(numr,mode)
	nx = image.get_xsize()
	ny = image.get_ysize()
	cnx = nx/2+1
	cny = ny/2+1

	M=image.get_xsize()
	# padd two times
	npad=2
	N=M*npad
	# support of the window
	K=6
	alpha=1.75
	r=M/2
	v=K/2.0/N
	kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
	refi=refim.FourInterpol(N,N,1,0)
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	q=Processor.EMFourierFilter(refi,params)
	refi=fft(q)
	crefim=Util.Polar2Dmi(refi,cnx,cny,numr,mode,kb)
	#info(crefim)
	Util.Frngs(crefim, numr)
	Applyws(crefim, numr,wr)

	imali=image.FourInterpol(2*M,2*M,1,0)
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	q=Processor.EMFourierFilter(imali,params)
	imali=fft(q)
	maxrin=numr[len(numr)-1]

	#print  maxrin
	line = EMData()
	line.set_size(maxrin,1,1)
	M=maxrin
	# do not pad
	npad=1
	N=M*npad
	# support of the window
	K=6
	alpha=1.75
	r=M/2
	v=K/2.0/N
	kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
	parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	data=[]
	data.insert(1,kbline)
	#dama=[]
	#dama.insert(1,kbline)

	peak = -1.0E23
	#qm=peak  # remove later
	for iy in xrange(-yrng,yrng+1,step):
		for  ix in xrange(-xrng,xrng+1,step):
			cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
			Util.Frngs(cimage, numr)
			qt = Util.Crosrng_msg(crefim,cimage,numr)
			# straight
			for i in xrange(0,maxrin): line[i]=qt[i,0]

			#  find the current maximum and its location
			ps=line.peak_search(1,1)
			#print  ps
			qn=ps[1]
			jtot=ps[2]  #/2
			q=Processor.EMFourierFilter(line,parline)
			data.insert(0,q)
			#info(q)
			#print  q.peak_search(1,1)
			#print  ix,iy
			#print  " before amoeba",ps[2]/2,q.get_pixel_conv(ps[2]/2, 0, 0, data[1])
			ps = amoeba([jtot], [2.0],afunc,1.e-4,1.e-4,500,data)
			del data[0]
			#print  ps
			jtot=ps[0][0]*2
			qn=ps[1]
			#print  qn,2*jtot*360/maxrin
			# mirror
			for i in xrange(0,maxrin): line[i]=qt[i,1]
			#print " MIRROR"
			#  find the current maximum and its location
			ps=line.peak_search(1,1)
			qm=ps[1]
			mtot=ps[3]/2
			q=Processor.EMFourierFilter(line,parline)
			data.insert(0,q)
			#print qm,mtot
			ps = amoeba([mtot], [2.0],afunc,1.e-4,1.e-4,500,data)
			del data[0]
			#print  qm,ps
			mtot=ps[0][0]*2
			qm=ps[1]
			#print  qm,mtot
	 
			if(qn >=peak or qm >=peak):
				if (qn >= qm):
					ang = ang_n(jtot+1, mode, numr[len(numr)-1])
					sx = -ix
					sy = -iy
					peak=qn
					mirror=0
				else:
					ang = ang_n(mtot+1, mode, numr[len(numr)-1])
					sx = -ix
					sy = -iy
					peak=qm
					mirror=1

      
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang,sxs,sys,mirror,peak    
	
	#postprocessing by amoeba search	
	del data[0]
	mask=model_circle(last_ring,nx,ny)
	data.insert(0,imali)
	data.insert(1,refim)
	data.insert(2,kb)
	data.insert(3,mask)
	ps = amoeba([ang,sxs,sys], [360.0/(2.0*pi*last_ring),1.0,1.0],dfunc,1.e-4,1.e-4,500,data)
	#print  ps
	#return  ps[0][0],ps[0][1],ps[0][2],mirror,-ps[1]
"""

def ormql(image,crefim,xrng,yrng,step,mode,numr,cnx,cny):
	"""
	Determine shift and rotation between image and reference image (refim)
	"""
	from math import pi, cos, sin
	from fundamentals import fft
	from utilities import amoeba, model_circle
	
	M=image.get_xsize()
	npad=2
	N=M*npad
	#support of the window
	K=6
	alpha=1.75
	r=M/2
	v=K/2.0/N
	kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)

	imali=image.FourInterpol(2*M,2*M,1,0)
	params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	q=Processor.EMFourierFilter(imali,params)
	imali=fft(q)
	
	maxrin=numr[len(numr)-1]

	#print  maxrin
	line = EMData()
	line.set_size(maxrin,1,1)
	M=maxrin
	# do not pad
	npad=1
	N=M*npad
	# support of the window
	K=6
	alpha=1.75
	r=M/2
	v=K/2.0/N
	kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
	parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	data=[]
	data.insert(1,kbline)

	peak = -1.0E23
	#qm=peak  # remove later
	for iy in xrange(-yrng,yrng+1,step):
		for  ix in xrange(-xrng,xrng+1,step):
			cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
			Util.Frngs(cimage, numr)
			qt = Util.Crosrng_msg(crefim,cimage,numr)
			
			# straight
			for i in xrange(0,maxrin): line[i]=qt[i,0]								
			#  find the current maximum and its location
			ps=line.peak_search(1,1)
			qn=ps[1]
			jtot=ps[2]/2
			q=Processor.EMFourierFilter(line,parline)
			data.insert(0,q)
			#info(q)
			#print  q.peak_search(1,1)
			#print  ix,iy
			#print  " before amoeba",ps[2]/2,q.get_pixel_conv(ps[2]/2, 0, 0, data[1])
			#print  " before amoeba",ps[2] ,q.get_pixel_conv(ps[2] , 0, 0, data[1])
			ps = amoeba([jtot], [2.0], oned_search_func,1.e-4,1.e-4,500,data)
			del data[0]
			#print  ps
			jtot=ps[0][0]*2
			qn=ps[1]
			#print  qn,2*jtot*360/maxrin
			
			# mirror
			for i in xrange(0,maxrin): line[i]=qt[i,1]
			#print " MIRROR"
			#  find the current maximum and its location
			ps=line.peak_search(1,1)
			# print ps
			qm=ps[1]
			mtot=ps[2]/2
			q=Processor.EMFourierFilter(line,parline)
			data.insert(0,q)
			#print qm,mtot
			ps = amoeba([mtot], [2.0],oned_search_func,1.e-4,1.e-4,500,data)
			del data[0]
			#print  qm,ps
			mtot=ps[0][0]*2
			qm=ps[1]
			#print  qm,mtot	 

			if(qn >=peak or qm >=peak):
				if (qn >= qm):
					ang = ang_n(jtot+1, mode, numr[len(numr)-1])
					sx = -ix
					sy = -iy
					peak=qn
					mirror=0
				else:
					ang = ang_n(mtot+1, mode, numr[len(numr)-1])
					sx = -ix
					sy = -iy
					peak=qm
					mirror=1
     
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang,sxs,sys,mirror,peak    	

def ormy(image,crefim,xrng,yrng,step,mode,numr,cnx,cny,interpolation_method=None):
	"""
	Determine shift and rotation between image and reference image (refim)
	It should be noted that crefim should be preprocessed before using this
	function
	"""
	from math import pi, cos, sin
	from fundamentals import fft
	from utilities import amoeba
	from sys import exit
	
	if interpolation_method==None:
		interpolation_method = interpolation_method_2D #use global setting
	if interpolation_method=="gridding":
		M=image.get_xsize()
		npad=2
		N=M*npad
		#support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)

		imali=image.FourInterpol(2*M,2*M,1,0)
		params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		q=Processor.EMFourierFilter(imali,params)
		imali=fft(q)
	
		maxrin=numr[len(numr)-1]
	
		#print  maxrin
		line = EMData()
		line.set_size(maxrin,1,1)
		M=maxrin
		# do not pad
		npad=1
		N=M*npad
		# support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
		parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		data=[]
		data.insert(1,kbline)
	elif interpolation_method=="quadratic":
		pass
	elif interpolation_method=="linear":
		pass
	else: 
		print "Error: Unknown interpolation method!"
		exit()

	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	
	if interpolation_method=="gridding":
		for i in xrange(-ky,ky+1):
			iy=i*step
			for  j in xrange(-kx,kx+1):
				ix=j*step
				cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
				Util.Frngs(cimage, numr)
				qt = Util.Crosrng_msg(crefim,cimage,numr)
				
				# straight
				for i in xrange(0,maxrin): line[i]=qt[i,0]
				#  find the current maximum and its location
				ps=line.peak_search(1,1)
				qn=ps[1]
				jtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([jtot], [2.0], oned_search_func, 1.e-4,1.e-4,500,data)
				del data[0]
				jtot=ps[0][0]*2
				qn=ps[1]
				
				# mirror
				for i in xrange(0,maxrin): line[i]=qt[i,1]
				# find the current maximum and its location
				ps=line.peak_search(1,1)
				qm=ps[1]
				mtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([mtot], [2.0],oned_search_func,1.e-4,1.e-4,500,data)
				del data[0]
				mtot=ps[0][0]*2
				qm=ps[1]

				if(qn >=peak or qm >=peak):
					if (qn >= qm):
						ang = ang_n(jtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qn
						mirror=0
					else:
						ang = ang_n(mtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qm
						mirror=1
	elif interpolation_method=="quadratic":
		for i in xrange(-ky, ky+1):
			iy = i*step
			for  j in xrange(-kx, kx+1):
				ix = j*step
				cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
				Util.Frngs(cimage, numr)
				retvals = Util.Crosrng_ms(crefim, cimage, numr)
				qn = retvals["qn"]
				qm = retvals["qm"]
				if(qn >=peak or qm >=peak):
					sx = -ix
					sy = -iy
					if (qn >= qm):
						ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
						peak=qn
						mirror=0
					else:
						ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
						peak=qm
						mirror=1		

	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	return  ang,sxs,sys,mirror,peak

def ormy2(image,refim,crefim,xrng,yrng,step,mode,numr,cnx,cny,interpolation_method=None):
	"""
	Determine shift and rotation between image and reference image (refim)
	It should be noted that crefim should be preprocessed before using this
	function.
	This function is mostly same as the ormy, the only difference is that 
	it has an ameoba at the end
	"""
	from math import pi, cos, sin
	from fundamentals import fft, mirror
	from utilities import amoeba, model_circle
	from sys import exit
	from alignment import ang_n
	from random import random
	
	if interpolation_method==None:
		interpolation_method = interpolation_method_2D #use global setting
		
	if interpolation_method=="gridding":
		M=image.get_xsize()
		npad=2
		N=M*npad
		#support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)

		imali=image.FourInterpol(2*M,2*M,1,0)
		params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		q=Processor.EMFourierFilter(imali,params)
		imali=fft(q)
	
		maxrin=numr[len(numr)-1]
		line = EMData()
		line.set_size(maxrin,1,1)
		M=maxrin
		# do not pad
		npad=1
		N=M*npad
		# support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
		parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		data=[]
		data.insert(1,kbline)
	elif interpolation_method=="quadratic":
		pass
	elif interpolation_method=="linear":
		pass
	else: 
		print "Error: Unknown interpolation method!"
		exit()

	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	
	if interpolation_method=="gridding":
		for i in xrange(-ky,ky+1):
			iy=i*step
			for  j in xrange(-kx,kx+1):
				ix=j*step
				cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
				Util.Frngs(cimage, numr)
				qt = Util.Crosrng_msg(crefim,cimage,numr)
				
				# straight
				for i in xrange(0,maxrin): line[i]=qt[i,0]					
				#  find the current maximum and its location
				ps=line.peak_search(1,1)				
				qn=ps[1]
				jtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([jtot], [2.0], oned_search_func, 1.e-4,1.e-4,500,data)
				del data[0]
				jtot=ps[0][0]*2
				qn=ps[1]

				# mirror
				for i in xrange(0,maxrin): line[i]=qt[i,1]
				#  find the current maximum and its location
				ps=line.peak_search(1,1)				
				qm=ps[1]
				mtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([mtot], [2.0], oned_search_func,1.e-4,1.e-4,500,data)
				del data[0]
				mtot=ps[0][0]*2
				qm=ps[1]

				if(qn >=peak or qm >=peak):
					if (qn >= qm):
						"""
						NOTICE: This is important!!!!
						
						The reason that there is a "+1" here while there is no "+1" in quadratic is that
						in program such as Crosrng_ms (used in quadratic), the returned position begins
						from 1 insteat of 0. Although this is kind of inconvenient, we decide to keep this 
						convention. Therefore, in function ang_n, there is a "-1" for offsetting. However, 
						for gridding, the program such as Crosrng_msg returns ccf. Also, we choose to have 
						the found position begin from 0, otherwise, it will become very complicated
						since it involves "*2" and "/2". Therefore, when using ang_n, we should have another
						"+1" to offset back.
						"""
						ang = ang_n(jtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qn
						is_mirror=0
					else:
						ang = ang_n(mtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qm
						is_mirror=1
	elif interpolation_method=="quadratic":
		for i in xrange(-ky, ky+1):
			iy = i*step
			for  j in xrange(-kx, kx+1):
				ix = j*step
				cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
				Util.Frngs(cimage, numr)
				retvals = Util.Crosrng_ms(crefim, cimage, numr)
				qn = retvals["qn"]
				qm = retvals["qm"]
				if(qn >=peak or qm >=peak):
					sx = -ix
					sy = -iy
					if (qn >= qm):
						ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
						peak=qn
						is_mirror=0
					else:
						ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
						peak=qm
						is_mirror=1		
	
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	
	last_ring = numr[len(numr)-3]
	nx = image.get_xsize()
	ny = image.get_ysize()
	mask = model_circle(last_ring,nx,ny)

	if interpolation_method=="gridding":
		if is_mirror:	
			M=image.get_xsize()
			image2 = mirror(image)
			imali=image2.FourInterpol(2*M,2*M,1,0)
			params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
			q=Processor.EMFourierFilter(imali,params)
			imali=fft(q)
		data.insert(0,imali)
		data.insert(1,refim)
		data.insert(2,kb)
		data.insert(3,mask)
		if is_mirror:
			ps = amoeba([-ang,-sxs,sys], [360.0/(2.0*pi*last_ring),step,step],dfunc,1.e-4,1.e-4,500,data)
		else:
			ps = amoeba([ang,sxs,sys], [360.0/(2.0*pi*last_ring),step,step],dfunc,1.e-4,1.e-4,500,data)
	elif interpolation_method=="quadratic":
		data = []
		if is_mirror:
			data.insert(0,mirror(image))
		else:
			data.insert(0,image)		
		data.insert(1,refim)
		data.insert(2,mask)
		if is_mirror:
			ps = amoeba([-ang,-sxs,sys], [360.0/(2.0*pi*last_ring),step,step],dfunc2,1.e-4,1.e-4,500,data)
		else:
			ps = amoeba([ang,sxs,sys], [360.0/(2.0*pi*last_ring),step,step],dfunc2,1.e-4,1.e-4,500,data)
	else: pass
	
	if ps[0][0] < 180: ps[0][0] = ps[0][0]+360
	if ps[0][0] > 180: ps[0][0] = ps[0][0]-360
	return  ps[0][0],ps[0][1],ps[0][2],is_mirror,-ps[1]


def ormy2lbfgsb(image,refim,crefim,xrng,yrng,step,mode,numr,cnx,cny,interpolation_method=None):
	"""
	Determine shift and rotation between image and reference image (refim)
	It should be noted that crefim should be preprocessed before using this
	function.
	This function is mostly same as the ormy2, the only difference is that 
	it use LBFGSB for parameter optimization
	"""
	from math import pi, cos, sin
	from fundamentals import fft, mirror
	from utilities import amoeba, model_circle
	from sys import exit
	from alignment import ang_n
	from scipy.optimize.lbfgsb import fmin_l_bfgs_b
	
	if interpolation_method==None:
		interpolation_method = interpolation_method_2D #use global setting
		
	if interpolation_method=="gridding":
		M=image.get_xsize()
		npad=2
		N=M*npad
		#support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)

		imali=image.FourInterpol(2*M,2*M,1,0)
		params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		q=Processor.EMFourierFilter(imali,params)
		imali=fft(q)
	
		maxrin=numr[len(numr)-1]
		line = EMData()
		line.set_size(maxrin,1,1)
		M=maxrin
		# do not pad
		npad=1
		N=M*npad
		# support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
		parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		data=[]
		data.insert(1,kbline)
	elif interpolation_method=="quadratic":
		pass
	elif interpolation_method=="linear":
		pass
	else: 
		print "Error: Unknown interpolation method!"
		exit()

	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	
	if interpolation_method=="gridding":
		for i in xrange(-ky,ky+1):
			iy=i*step
			for  j in xrange(-kx,kx+1):
				ix=j*step
				cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
				Util.Frngs(cimage, numr)
				qt = Util.Crosrng_msg(crefim,cimage,numr)
				
				# straight
				for i in xrange(0,maxrin): line[i]=qt[i,0]					
				#  find the current maximum and its location
				ps=line.peak_search(1,1)				
				qn=ps[1]
				jtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([jtot], [2.0], oned_search_func, 1.e-4,1.e-4,500,data)
				del data[0]
				jtot=ps[0][0]*2
				qn=ps[1]

				# mirror
				for i in xrange(0,maxrin): line[i]=qt[i,1]
				#  find the current maximum and its location
				ps=line.peak_search(1,1)				
				qm=ps[1]
				mtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([mtot], [2.0], oned_search_func,1.e-4,1.e-4,500,data)
				del data[0]
				mtot=ps[0][0]*2
				qm=ps[1]

				if(qn >=peak or qm >=peak):
					if (qn >= qm):
						ang = ang_n(jtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qn
						is_mirror=0
					else:
						ang = ang_n(mtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qm
						is_mirror=1
	elif interpolation_method=="quadratic":
		for i in xrange(-ky, ky+1):
			iy = i*step
			for  j in xrange(-kx, kx+1):
				ix = j*step
				cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
				Util.Frngs(cimage, numr)
				retvals = Util.Crosrng_ms(crefim, cimage, numr)
				qn = retvals["qn"]
				qm = retvals["qm"]
				if(qn >=peak or qm >=peak):
					sx = -ix
					sy = -iy
					if (qn >= qm):
						ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
						peak=qn
						is_mirror=0
					else:
						ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
						peak=qm
						is_mirror=1		
	
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co	
	
	last_ring = numr[len(numr)-3]
	nx = image.get_xsize()
	ny = image.get_ysize()
	mask = model_circle(last_ring,nx,ny)

	if interpolation_method=="gridding":
		if is_mirror:	
			M=image.get_xsize()
			image2 = mirror(image)
			imali=image2.FourInterpol(2*M,2*M,1,0)
			params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
			q=Processor.EMFourierFilter(imali,params)
			imali=fft(q)
			#ps = Util.twoD_fine_ali_G(imali, refim, mask, kb, -ang, -sxs, sys);
			x0 = [-ang, -sxs, sys] 
			bounds = [(x0[0]-2.0, x0[0]+2.0), (x0[1]-1.5, x0[1]+1.5), (x0[2]-1.5, x0[2]+1.5)]
			data = []
			data.append(imali)
			data.append(refim)
			data.append(kb)
			data.append(mask)
			ps, val, d = fmin_l_bfgs_b(dfunc_i, x0, args=[data], approx_grad=1, bounds=bounds, m=10, factr=1e1, pgtol=1e-5, epsilon=1e-3, iprint=-1, maxfun=15000)
		else:
			#ps = Util.twoD_fine_ali_G(imali, refim, mask, kb, ang, sxs, sys);			
			x0 = [ang, sxs, sys] 
			bounds = [(x0[0]-2.0, x0[0]+2.0), (x0[1]-1.5, x0[1]+1.5), (x0[2]-1.5, x0[2]+1.5)]
			data = []
			data.append(imali)
			data.append(refim)
			data.append(kb)
			data.append(mask)
			ps, val, d = fmin_l_bfgs_b(dfunc_i, x0, args=[data], approx_grad=1, bounds=bounds, m=10, factr=1e1, pgtol=1e-5, epsilon=1e-3, iprint=-1, maxfun=15000)
	elif interpolation_method=="quadratic":
		if is_mirror:
			image=mirror(image)
			#ps = Util.twoD_fine_ali(image, refim, mask, -ang, -sxs, sys)
			x0 = [-ang, -sxs, sys] 
			bounds = [(x0[0]-2.0, x0[0]+2.0), (x0[1]-1.5, x0[1]+1.5), (x0[2]-1.5, x0[2]+1.5)]
			data = []
			data.append(image)
			data.append(refim)
			data.append(mask)
			ps, val, d = fmin_l_bfgs_b(dfunc2_i, x0, args=[data], approx_grad=1, bounds=bounds, m=10, factr=1e1, pgtol=1e-5, epsilon=1e-3, iprint=-1, maxfun=15000)
		else:
			#ps = Util.twoD_fine_ali(image, refim, mask, ang, sxs, sys)
			x0 = [ang, sxs, sys] 
			bounds = [(x0[0]-2.0, x0[0]+2.0), (x0[1]-1.5, x0[1]+1.5), (x0[2]-1.5, x0[2]+1.5)]
			data = []
			data.append(image)
			data.append(refim)
			data.append(mask)			
			ps, val, d = fmin_l_bfgs_b(dfunc2_i, x0, args=[data], approx_grad=1, bounds=bounds, m=10, factr=1e1, pgtol=1e-5, epsilon=1e-3, iprint=-1, maxfun=15000)
	else: pass

	if ps[0] < 180: ps[0] = ps[0]+360
	if ps[0] > 180: ps[0] = ps[0]-360
	return  ps[0], ps[1], ps[2], is_mirror


def ormy2sd(image,refim,crefim,xrng,yrng,step,mode,numr,cnx,cny,interpolation_method=None):
	"""
	Determine shift and rotation between image and reference image (refim)
	It should be noted that crefim should be preprocessed before using this
	function.
	This function is mostly same as the ormy2, the only difference is that 
	it use steepest descent algorithm for parameter optimization
	"""
	from math import pi, cos, sin
	from fundamentals import fft, mirror
	from utilities import amoeba, model_circle
	from sys import exit
	from alignment import ang_n
	
	if interpolation_method==None:
		interpolation_method = interpolation_method_2D #use global setting
		
	if interpolation_method=="gridding":
		M=image.get_xsize()
		npad=2
		N=M*npad
		#support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)

		imali=image.FourInterpol(2*M,2*M,1,0)
		params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		q=Processor.EMFourierFilter(imali,params)
		imali=fft(q)
	
		maxrin=numr[len(numr)-1]
		line = EMData()
		line.set_size(maxrin,1,1)
		M=maxrin
		# do not pad
		npad=1
		N=M*npad
		# support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
		parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		data=[]
		data.insert(1,kbline)
	elif interpolation_method=="quadratic":
		pass
	elif interpolation_method=="linear":
		pass
	else: 
		print "Error: Unknown interpolation method!"
		exit()

	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2
	
	if interpolation_method=="gridding":
		for i in xrange(-ky,ky+1):
			iy=i*step
			for  j in xrange(-kx,kx+1):
				ix=j*step
				cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
				Util.Frngs(cimage, numr)
				qt = Util.Crosrng_msg(crefim,cimage,numr)
				
				# straight
				for i in xrange(0,maxrin): line[i]=qt[i,0]					
				#  find the current maximum and its location
				ps=line.peak_search(1,1)				
				qn=ps[1]
				jtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([jtot], [2.0], oned_search_func, 1.e-4,1.e-4,500,data)
				del data[0]
				jtot=ps[0][0]*2
				qn=ps[1]

				# mirror
				for i in xrange(0,maxrin): line[i]=qt[i,1]
				#  find the current maximum and its location
				ps=line.peak_search(1,1)				
				qm=ps[1]
				mtot=ps[2]/2
				q=Processor.EMFourierFilter(line,parline)
				data.insert(0,q)
				ps = amoeba([mtot], [2.0], oned_search_func,1.e-4,1.e-4,500,data)
				del data[0]
				mtot=ps[0][0]*2
				qm=ps[1]

				if(qn >=peak or qm >=peak):
					if (qn >= qm):
						ang = ang_n(jtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qn
						is_mirror=0
					else:
						ang = ang_n(mtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak=qm
						is_mirror=1
	elif interpolation_method=="quadratic":
		for i in xrange(-ky, ky+1):
			iy = i*step
			for  j in xrange(-kx, kx+1):
				ix = j*step
				cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
				Util.Frngs(cimage, numr)
				retvals = Util.Crosrng_ms(crefim, cimage, numr)
				qn = retvals["qn"]
				qm = retvals["qm"]
				if(qn >=peak or qm >=peak):
					sx = -ix
					sy = -iy
					if (qn >= qm):
						ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
						peak=qn
						is_mirror=0
					else:
						ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
						peak=qm
						is_mirror=1		
	
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co	
	
	last_ring = numr[len(numr)-3]
	nx = image.get_xsize()
	ny = image.get_ysize()
	mask = model_circle(last_ring,nx,ny)

	if interpolation_method=="gridding":
		if is_mirror:	
			M=image.get_xsize()
			image2 = mirror(image)
			imali=image2.FourInterpol(2*M,2*M,1,0)
			params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
			q=Processor.EMFourierFilter(imali,params)
			imali=fft(q)
			ps = Util.twoD_fine_ali_SD_G(imali, refim, mask, kb, -ang, -sxs, sys);
		else:
			ps = Util.twoD_fine_ali_SD_G(imali, refim, mask, kb, ang, sxs, sys);			
	elif interpolation_method=="quadratic":
		if is_mirror:
			image=mirror(image)
			ps = Util.twoD_fine_ali_SD(image, refim, mask, -ang, -sxs, sys)
		else:
			ps = Util.twoD_fine_ali_SD(image, refim, mask, ang, sxs, sys)
	else: pass

	if ps[0] < 180: ps[0] = ps[0]+360
	if ps[0] > 180: ps[0] = ps[0]-360
	return  ps[0], ps[1], ps[2], is_mirror, ps[3]


def ormy3(image,crefim,xrng,yrng,step,mode,numr,cnx,cny,interpolation_method=None):
	"""
	Determine shift and rotation between image and reference image (refim)
	
	It should be noted that crefim should be preprocessed before using this	function.
	
	This function is mostly same as the ormy2, the difference is that is use a different 
	strategy for refinement. To be specific, after the coarse search, it refines [sx, sy] 
	instead of refining [ang, sx, sy]. 
	
	In the future, we can delete ormy and ormy2 if this version is proved to be stable.
	"""
	from math import pi, cos, sin
	from fundamentals import fft, mirror
	from utilities import amoeba2, model_circle, amoeba
	from sys import exit
	from alignment import ang_n
	
	if interpolation_method==None:
		interpolation_method = interpolation_method_2D #use global setting
		
	if interpolation_method=="gridding":
		M=image.get_xsize()
		npad=2
		N=M*npad
		#support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)

		imali=image.FourInterpol(2*M,2*M,1,0)
		params = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		q=Processor.EMFourierFilter(imali,params)
		imali=fft(q)
	
		maxrin=numr[len(numr)-1]
		M=maxrin
		# do not pad
		npad=1
		N=M*npad
		# support of the window
		K=6
		alpha=1.75
		r=M/2
		v=K/2.0/N
		kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
		parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
		data=[]
		data.insert(1,kbline)
	elif interpolation_method=="quadratic":
		pass
	elif interpolation_method=="linear":
		pass
	else: 
		print "Error: Unknown interpolation method!"
		exit()

	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2

	if interpolation_method=="gridding":
		for i in xrange(-ky,ky+1):
			iy=i*step
			for  j in xrange(-kx,kx+1):
				ix=j*step
				cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
				Util.Frngs(cimage, numr)
				
				# straight, find the current maximum and its location
				line_s = Util.Crosrng_msg_s(crefim,cimage,numr)
				ps=line_s.peak_search(1,1)				
				qn=ps[1]
				jtot=ps[2]/2
				q=Processor.EMFourierFilter(line_s,parline)
				data.insert(0,q)
				ps = amoeba([jtot], [2.0], oned_search_func, 1.e-4,1.e-4,500,data)
				del data[0]
				jtot=ps[0][0]*2
				qn=ps[1]

				# mirror, find the current maximum and its location
				line_m = Util.Crosrng_msg_m(crefim,cimage,numr)
				ps=line_m.peak_search(1,1)				
				qm=ps[1]
				mtot=ps[2]/2
				q=Processor.EMFourierFilter(line_m,parline)
				data.insert(0,q)
				ps = amoeba([mtot], [2.0], oned_search_func,1.e-4,1.e-4,500,data)
				del data[0]
				mtot=ps[0][0]*2
				qm=ps[1]

				if(qn >=peak or qm >=peak):
					if (qn >= qm):
						ang = ang_n(jtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak = qn
						is_mirror=0
					else:
						ang = ang_n(mtot+1, mode, numr[len(numr)-1])
						sx = -ix
						sy = -iy
						peak = qm
						is_mirror=1
		data0 = []
		data0.insert(0,imali)
		data0.insert(1,cnx)
		data0.insert(2,cny)
		data0.insert(3,numr)
		data0.insert(4,mode)
		data0.insert(5,kb)
		data0.insert(6,crefim)
		data0.insert(7,parline)
		data0.insert(8,maxrin)
		data0.insert(9,kbline)
		data0.insert(10,is_mirror)
		
		ps2 = amoeba2([-sx,-sy],[1,1],func_loop2,1.e-4,1.e-4,500,data0)
		
		if ps2[1] > peak:
			sx = -ps2[0][0]
			sy = -ps2[0][1]
			ang = ps2[3]
	elif interpolation_method=="quadratic":
		for i in xrange(-ky, ky+1):
			iy = i*step
			for  j in xrange(-kx, kx+1):
				ix = j*step
				cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
				Util.Frngs(cimage, numr)
				retvals = Util.Crosrng_ms(crefim, cimage, numr)
				qn = retvals["qn"]
				qm = retvals["qm"]
				if(qn >=peak or qm >=peak):
					sx = -ix
					sy = -iy
					if (qn >= qm):
						ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
						peak=qn
						is_mirror=0
					else:
						ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
						peak=qm
						is_mirror=1	 
		
		data = []
		data.insert(0,image)
		data.insert(1,cnx)
		data.insert(2,cny)
		data.insert(3,numr)
		data.insert(4,mode)
		data.insert(5,crefim)
		ps2 = amoeba2([-sx,-sy],[1,1],func_loop,1.e-4,1.e-4,500,data)
		if ps2[1]>peak:
			sx = -ps2[0][0]
			sy = -ps2[0][1]
			ang = ps2[3]
		
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	if is_mirror:
		ang = -ang
		sxs = -sxs	
	return  ang,sxs,sys,is_mirror,peak	

def ormy3g(imali,kb,crefim,xrng,yrng,step,mode,numr,cnx,cny):
	"""
	Determine shift and rotation between image and reference image (refim)
	
	It should be noted that crefim should be preprocessed before using this	function.
	
	This function is mostly same as the ormy2, the difference is that is use a different 
	strategy for refinement. To be specific, after the coarse search, it refines [sx, sy] 
	instead of refining [ang, sx, sy]. 
	
	In the future, we can delete ormy and ormy2 if this version is proved to be stable.
	
	This version is only used for gridding interpolation and assume imali is alread prepared.
	"""
	from math import pi, cos, sin
	from fundamentals import fft, mirror
	from utilities import amoeba, model_circle, amoeba2
	from sys import exit
	
	maxrin=numr[len(numr)-1]
	M=maxrin
	# do not pad
	npad=1
	N=M*npad
	# support of the window
	K=6
	alpha=1.75
	r=M/2
	v=K/2.0/N
	kbline = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
	parline = {"filter_type" : Processor.fourier_filter_types.KAISER_SINH_INVERSE,"alpha" : alpha, "K":K,"r":r,"v":v,"N":N}
	data=[]
	data.insert(1,kbline)

	peak = -1.0E23
	ky = int(2*yrng/step+0.5)//2
	kx = int(2*xrng/step+0.5)//2

	for i in xrange(-ky,ky+1):
		iy=i*step
		for  j in xrange(-kx,kx+1):
			ix=j*step
			cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
			Util.Frngs(cimage, numr)
			
			# straight, find the current maximum and its location
			line_s = Util.Crosrng_msg_s(crefim,cimage,numr)
			ps=line_s.peak_search(1,1)				
			qn=ps[1]
			jtot=ps[2]/2
			q=Processor.EMFourierFilter(line_s,parline)
			data.insert(0,q)
			ps = amoeba([jtot], [2.0], oned_search_func, 1.e-4,1.e-4,500,data)
			del data[0]
			jtot=ps[0][0]*2
			qn=ps[1]

			# mirror, find the current maximum and its location
			line_m = Util.Crosrng_msg_m(crefim,cimage,numr)
			ps=line_m.peak_search(1,1)				
			qm=ps[1]
			mtot=ps[2]/2
			q=Processor.EMFourierFilter(line_m,parline)
			data.insert(0,q)
			ps = amoeba([mtot], [2.0], oned_search_func,1.e-4,1.e-4,500,data)
			del data[0]
			mtot=ps[0][0]*2
			qm=ps[1]

			if(qn >=peak or qm >=peak):
				if (qn >= qm):
					ang = ang_n(jtot+1, mode, numr[len(numr)-1])
					sx = -ix
					sy = -iy
					peak = qn
					is_mirror=0
				else:
					ang = ang_n(mtot+1, mode, numr[len(numr)-1])
					sx = -ix
					sy = -iy
					peak = qm
					is_mirror=1

	data0 = []
	data0.insert(0,imali)
	data0.insert(1,cnx)
	data0.insert(2,cny)
	data0.insert(3,numr)
	data0.insert(4,mode)
	data0.insert(5,kb)
	data0.insert(6,crefim)
	data0.insert(7,parline)
	data0.insert(8,maxrin)
	data0.insert(9,kbline)
	data0.insert(10,is_mirror)
	
	ps2 = amoeba2([-sx,-sy],[1,1],func_loop2,1.e-4,1.e-4,500,data0)
	if ps2[1]>peak:
		sx = -ps2[0][0]
		sy = -ps2[0][1]
		ang = ps2[3]
				
	co =  cos(ang*pi/180.0)
	so = -sin(ang*pi/180.0)
	sxs = sx*co - sy*so
	sys = sx*so + sy*co
	if is_mirror:
		ang = -ang
		sxs = -sxs	
	return  ang,sxs,sys,is_mirror,peak	


def func_loop(args, data):
	from alignment import ang_n

	image = data[0]
	cnx = data[1]
	cny = data[2]
	numr = data[3]
	mode = data[4]
	crefim = data[5]
	ix = args[0]
	iy = args[1]
	cimage=Util.Polar2Dm(image, cnx+ix, cny+iy, numr, mode)
	Util.Frngs(cimage, numr)
	retvals = Util.Crosrng_ms(crefim, cimage, numr)
	qn = retvals["qn"]
	qm = retvals["qm"]
	if qn>=qm :
		ang = ang_n(retvals["tot"], mode, numr[len(numr)-1])
		return qn, ang
	else :
		ang = ang_n(retvals["tmt"], mode, numr[len(numr)-1])
		return qm, ang

		
def func_loop2(args, data):
	from utilities import amoeba
	from alignment import ang_n
	
	imali = data[0]
	cnx = data[1]
	cny = data[2]
	numr = data[3]
	mode = data[4]
	kb = data[5]
	crefim = data[6]
	parline = data[7]
	maxrin = data[8]
	kbline = data[9]
	is_mirror = data[10]
	data1 = []
	data1.insert(1,kbline)
	
	ix = args[0]
	iy = args[1]
	
	cimage=Util.Polar2Dmi(imali,cnx+ix,cny+iy,numr,mode,kb)
	Util.Frngs(cimage, numr)
	
	if is_mirror==0:
		line = Util.Crosrng_msg_s(crefim,cimage,numr)
		#  Straight, find the current maximum and its location
		ps=line.peak_search(1,1)				
		jtot=ps[2]/2
		q=Processor.EMFourierFilter(line,parline)
		data1.insert(0,q)
		ps = amoeba([jtot], [2.0], oned_search_func, 1.e-4,1.e-4,500,data1)
		del data1[0]
		jtot = ps[0][0]*2
		qn = ps[1]
		ang = ang_n(jtot+1, mode, numr[len(numr)-1])				
		return qn, ang
	else:
		line = Util.Crosrng_msg_m(crefim,cimage,numr)
		#  Mirror, find the current maximum and its location
		ps=line.peak_search(1,1)				
		mtot=ps[2]/2
		q=Processor.EMFourierFilter(line,parline)
		data1.insert(0,q)
		ps = amoeba([mtot], [2.0], oned_search_func,1.e-4,1.e-4,500,data1)	
		del data1[0]
		mtot=ps[0][0]*2
		qm=ps[1]
		ang = ang_n(mtot+1, mode, numr[len(numr)-1])				
		return qm, ang

'''
def proj_ali(volref, mask, projdata, first_ring, last_ring, rstep, xrng, yrng, step, dtheta, ref_a, sym, CTF = False):
	from utilities    import even_angles, model_circle, dropSpiderDoc, info
	from projection   import prgs
	from fundamentals import prepg
	from statistics   import ttime
	from math import cos
	from string import split

	print  ttime()
	mode    = "F"
	if(CTF): parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
	# generate list of Eulerian angles for reference projections
	#  phi, theta, psi
	tmp_sym = split(sym)
	if(tmp_sym[0][0]=="d" or tmp_sym[0][0]=="D"): nfold = int(tmp_sym[0][1])*2
	else:                                       nfold = int(tmp_sym[0][1])
	ref_angles = even_angles(dtheta, 0.0, 90.0, 0.0, 359.99/nfold, ref_a, "Zero")
	#dropSpiderDoc("angles.txt",ref_angles)
	num_ref = len(ref_angles)
	# generate reference projections in polar coords
	#  begin from applying the mask, i.e., subtract the average under the mask and multiply by the mask
	#print "volref"
	#info(volref)
	if(mask):
		[mean, sigma, xmin, xmax ] =  Util.infomask(volref, mask)

		volref -= mean
		Util.mul_img(volref, mask)

	nx=volref.get_xsize()
	ny=volref.get_ysize()
	#  center is in SPIDER convention
	cnx = int(nx/2)+1
	cny = int(ny/2)+1
	#precalculate rings
	numr=Numrinit(first_ring, last_ring, rstep, mode)
	wr = ringwe(numr ,mode)
	# K-B
	kb=kbt(nx)
	# prepare the reference volume
	volrefft = prep_vol_kb(volref,kb)
	print  ttime()

	# prepare 2-D ask for normalization
	mask2D = model_circle(last_ring, nx, ny)
	if(first_ring > 0):
		prjref = model_circle(first_ring, nx, ny)
		mask2D -= prjref

	ref_proj_rings = []     # list of (image objects) reference projections in Fourier representation
	# loop over reference angles
	for i in xrange(num_ref):
		params = [ref_angles[i][0],ref_angles[i][1],ref_angles[i][2],0.0,0.0]
		#print  params
		prjref = prgs(volrefft, kb, params)

		prjref.process_inplace("normalize.mask", {"mask":mask2D, "no_sigma":1})  # (i-a)/s
		#prjref.write_image("prj.spi",i)
		#info(prjref)
		#temp   = prepg(prjref, kb)
		#cimage = Util.Polar2Dmi(temp, cnx, cny, numr, mode, kb)
		cimage=Util.Polar2Dm(prjref, cnx, cny, numr, mode)
		Util.Frngs(cimage, numr)  # currently set to gridding....
		Applyws(cimage, numr, wr)
		ref_proj_rings.insert(i, cimage)
		#info(ref_proj_rings[i])

	exptimage = EMData()
	#  find out how many images there are in the stack
	nprojdata = EMUtil.get_image_count(projdata)
	for imn in xrange(nprojdata):
		print  imn, ttime()
		exptimage.read_image(projdata, imn)
		if(CTF):
			ctf_params = get_arb_params(e, parnames)
			if(ctf_params[6] == 0):
				from filter import filt_ctf
				exptimage = filt_ctf(exptimage, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], -1, ctf_params[5])
		#pg = prepg(exptimage, kb)
		#phi1 = exptimage.get_attr('phi')
		#theta1 = exptimage.get_attr('theta')
		#psi1 = exptimage.get_attr('psi')
		sxo = exptimage.get_attr('s2x')
		syo = exptimage.get_attr('s2y')
		peak = -1.0E23
		for i in xrange(num_ref):
			#print  "REFERENCE IMAGE:  ",i,"  ",ttime()
			#info(ref_proj_rings[i])
			[angt,sxst,syst,mirrort,peakt] = ormq(exptimage, ref_proj_rings[i], xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
			#print angt,sxst,syst,mirrort,peakt

			#print  "RESULT:  ",i, angt, sxst, syst, mirrort, peakt
			if(peakt>peak):
				peak   = peakt
				numref = i
				ang    = -angt
				sxs    = sxst
				sys    = syst
				mirror = mirrort
		ang = (ang+360.0)%360.0
		if  mirror:
			# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
			#  What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
			#print  imn," M ",ang,numref,ref_angles[numref],-sxs+sxo,-sys+syo
			exptimage.set_attr_dict({'phi':(ref_angles[numref][0]+180.0)%360.0, 'theta':180-ref_angles[numref][1], 'psi':(180+ref_angles[numref][2]-ang+360.0)%360.0, 'sx':-sxs+sxo, 'sy':-sys+syo})
		else:
			#print  imn,"   ",ang,numref,ref_angles[numref],sxs+sxo,sys+syo
			exptimage.set_attr_dict({'phi':ref_angles[numref][0], 'theta':ref_angles[numref][1], 'psi':(ref_angles[numref][2]+ang+360.0)%360.0, 's2x':sxs+sxo, 's2y':sys+syo})
		exptimage.write_image(projdata, imn, EMUtil.ImageType.IMAGE_HDF, True)
'''



'''
#  This version has gridding projections
def proj_ali_incore(volref, mask3D, projdata, first_ring, last_ring, rstep, xrng, yrng, step, delta, ref_a, symmetry, CTF = False):
	from alignment    import apmq
	from utilities    import even_angles, model_circle, compose_transform2
	from projection   import prgs
	from fundamentals import prepg

	#from sys import exit
	from utilities    import dropImage,info
	from statistics import memory
	initmem = memory()
	print  initmem/1.0e6
	mode    = "F"
	if(CTF): parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
	# generate list of Eulerian angles for reference projections
	#  phi, theta, psi
	ref_angles = even_angles(delta, symmetry = symmetry, method = ref_a, phiEqpsi = "Zero")
	#from utilities import dropSpiderDoc
	#dropSpiderDoc("angles.txt",ref_angles)
	num_ref = len(ref_angles)
	# generate reference projections in polar coords
	#  begin from applying the mask, i.e., subtract the average under the mask and multiply by the mask
	if(mask3D):
		[mean, sigma, xmin, xmax ] =  Util.infomask(volref, mask3D, True)
		volref -= mean
		Util.mul_img(volref, mask3D)
	#dropImage(volref, "volref.spi", "s")
	#exit()
	nx   = volref.get_xsize()
	ny   = volref.get_ysize()
	#  center is in SPIDER convention
	cnx  = int(nx/2)+1
	cny  = int(ny/2)+1
	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
	wr   = ringwe(numr ,mode)
	# K-B
	kb   = kbt(nx)
	# prepare the reference volume
	volrefft = prep_vol_kb(volref,kb)
	#print  ttime()

	# prepare 2-D ask for normalization
	mask2D = model_circle(last_ring, nx, ny)
	if(first_ring > 0):
		prjref = model_circle(first_ring, nx, ny)
		mask2D -= prjref

	print  " pro_ali before refproj ",memory(initmem)/1.0e6,num_ref
	ref_proj_rings = []     # list of (image objects) reference projections in Fourier representation
	# loop over reference angles
	for i in xrange(num_ref):
		params = [ref_angles[i][0], ref_angles[i][1], ref_angles[i][2], 0.0,0.0]
		#print  params
		prjref = prgs(volrefft, kb, params)
		#from utilities import get_im
		#prjref = get_im('projspi.spi',i)
		prjref.process_inplace("normalize.mask", {"mask":mask2D, "no_sigma":1})  # (i-a)/s
		#prjref.write_image("prjsparx_n.spi",i)
		#info(prjref)
		#temp   = prepg(prjref, kb)
		#cimage = Util.Polar2Dmi(temp, cnx, cny, numr, mode, kb)
		cimage=Util.Polar2Dm(prjref, cnx, cny, numr, mode)
		Util.Frngs(cimage, numr)  # currently set to quadratic/gridding....
		Applyws(cimage, numr, wr)
		ref_proj_rings.append(cimage)
		if(i == 0):  info(cimage)
		#info(ref_proj_rings[i])
	print  " pro_ali after refproj ",memory(initmem)/1.0e6
	#exit()
	#from utilities  import ttime
	#print  ttime()
	#soto = []
	for imn in xrange(len(projdata)):
		#pg = prepg(exptimage, kb)
		sxo = projdata[imn].get_attr('s2x')
		syo = projdata[imn].get_attr('s2y')
		#peak = -1.0E23
		# new
		[ang, sxs, sys, mirror, nref, peak] = Util.multiref_polar_ali_2d(projdata[imn], ref_proj_rings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
		numref=int(nref)
		#[ang,sxs,sys,mirror,peak,numref] = apmq(projdata[imn], ref_proj_rings, xrng, yrng, step, mode, numr, cnx-sxo, cny-syo)
		#ang = (ang+360.0)%360.0
		# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
		#  What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
		angb, sxb, syb, ct = compose_transform2(0.0, sxs, sys, 1,  -ang, 0.,0.,1)
		if  mirror:
			#print  imn," M ",ang,numref,ref_angles[numref],-sxs+sxo,-sys+syo
			projdata[imn].set_attr_dict({'phi':(ref_angles[numref][0]+540.0)%360.0, 'theta':180.0-ref_angles[numref][1], 'psi':(540.0-ref_angles[numref][2]+angb)%360.0, 's2x':sxb+sxo, 's2y':syb+syo})
		else:
			#print  imn,"   ",ang,numref,ref_angles[numref],sxs+sxo,sys+syo
			projdata[imn].set_attr_dict({'phi':ref_angles[numref][0], 'theta':ref_angles[numref][1], 'psi':(ref_angles[numref][2]+angb+360.0)%360.0, 's2x':sxb+sxo, 's2y':syb+syo})
	print  " pro_ali after apmq ",memory(initmem)/1.0e6
	#print  ttime()
	#from sys import exit
	#exit()
'''

def ref_3d_ali(image, mask, volref, currentparams):
	from projection import prep_vol
	from utilities  import amoeba
	# currentparams: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy.
	data=[]
	volft,kb=prep_vol(volref)
	data.insert(0,volft)
	data.insert(1,kb)
	data.insert(2,image)
	data.insert(3,mask)
	#print  eqproj(currentparams,data)
	#return amoeba(currentparams, [1.0,1.0,1.0,0.5,0.5],eqproj,1.e-4,1.e-4,500,data)
	return amoeba(currentparams, [2.0,2.0,2.0,1.0,1.0],eqproj,1.e-4,1.e-4,500,data)

def ref_ali(volref, mask3D, mask, stack_name, list_of_particles, trans_params, angles, delta):
	from projection import prep_vol
	from utilities  import amoeba,info
	from math       import pi
	from time       import time
	# currentparams: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy, mirror, peak
	# 
	#[mean, sigma, xmin, xmax, nx, ny, nz ] =  info(volref,mask3D)
	#volref=(volref-mean)*mask3D

	data=[]
	volft,kb=prep_vol(volref)
	data.insert(0,volft)
	data.insert(1,kb)
	data.insert(3,mask)
	image=EMData()
	newp = []
	for i in xrange (0,len(list_of_particles)):
		imn=list_of_particles[i]
		#print  "  Stack: ",stack_name,"  image number =",imn," time: ",time()
		image.read_image(stack_name,imn)
		#info(image)
		#temp=aptrans(image,trans_params[4*imn:4*imn+4])
		#temp=Util.window(image,81,81)
		data.insert(2,image)
		#info(temp)
		#data.insert(2,aptrans(image,trans_params[4*imn:4*imn+4]))
		
		# atparams: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy, mirror, peak
		atparams = [angles[imn][0],angles[imn][1],angles[imn][2],0.0,0.0]
		initial = eqproj(atparams,data) # DDDDDDDDDDDDDDDDDDD
		stheta = abs(sin(atparams[1]*pi/180.0))
		if(stheta >0.0):
			weight_phi=min(180.0,delta/stheta/2.0)
		else:
			weight_phi=180.0
		#print  delta,weight_phi,time()
		#print  atparams,eqproj(atparams,data)
		params =  amoeba(atparams, [weight_phi,delta,weight_phi,1.0,1.0],eqproj,1.e-4,1.e-4,500,data)
		del  data[2]
		print "ref_ali -- imn:", imn, "initial:", initial, "params[1]:", params[1]  # DDDDDDDDDDDDDDDDDDD
		newp.append([params[0][0],params[0][1],params[0][2],params[0][3],params[0][4]])
	return  newp

def ref_3d_ali(image,mask,volref,currentparams):
	from projection import prep_vol
	from utilities import amoeba
	data=[]
	volft,kb=prep_vol(volref)
	data.insert(0,volft)
	data.insert(1,kb)
	data.insert(2,image)
	data.insert(3,mask)
	print  eqproj(currentparams,data)
	#return amoeba(currentparams, [1.0,1.0,1.0,0.5,0.5],eqproj,1.e-4,1.e-4,500,data)
	return amoeba(currentparams, [2.0,2.0,2.0,1.0,1.0],eqproj,1.e-4,1.e-4,500,data)


# this is a new version of ref_ali where params are in the header, no CTF for the time being
def ref_alis(volref, mask3D, mask, stack_name, list_of_particles, delta):
	from projection import prep_vol
	from utilities import amoeba,info
	from math import pi
	from time import time
	# 
	#[mean, sigma, xmin, xmax, nx, ny, nz ] =  info(volref,mask3D)
	#volref=(volref-mean)*mask3D

	data=[]
	volft,kb=prep_vol(volref)
	data.insert(0,volft)
	data.insert(1,kb)
	data.insert(3,mask)
	image=EMData()
	for i in xrange (0,len(list_of_particles)):
		imn=list_of_particles[i]
		#print  "  Stack: ",stack_name,"  image number =",imn," time: ",time()
		image.read_image(stack_name,imn)
		phi   = image.get_attr('phi')
		theta = image.get_attr('theta')
		psi   = image.get_attr('psi')
		#  have to invert the sign, as now the shift is applied to the projection, not to the image
		sx = -image.get_attr('sx')
		sy = -image.get_attr('sy')
		data.insert(2,image)
		# atparams: 0 - phi, 1 - theta, 2 - psi, 3 - sx, 4 - sy, mirror, peak
		atparams = [phi,theta,psi,sx,sy]
		print atparams
		initial = eqproj(atparams,data) # DDDDDDDDDDDDDDDDDDD
		stheta = abs(sin(atparams[1]*pi/180.0))
		if(stheta >0.0):
			weight_phi=min(180.0,delta/stheta/2.0)
		else:
			weight_phi=180.0
		#print  delta,weight_phi,time()
		#print  atparams,eqproj(atparams,data)
		params =  amoeba(atparams, [weight_phi,delta,weight_phi,1.0,1.0],eqproj,1.e-4,1.e-4,500,data)
		print params[0][0],params[0][1],params[0][2],params[0][3],params[0][4]
		del  data[2]
		print "ref_ali -- imn:", imn, "initial:", initial, "params[1]:", params[1],params[2]  # DDDDDDDDDDDDDDDDDDD
		image.set_attr_dict({'phi':params[0][0], 'theta':params[0][1], 'psi':params[0][2], 'sx':-params[0][3], 'sy':-params[0][4]})
		image.write_image(stack_name, i, EMUtil.ImageType.IMAGE_HDF, True)
	return


def ref_3d_ali_xyz(image,mask,volref,currentparams):
	from projection import prep_vol
	from utilities import amoeba
	EULER_XYZ=Transform3D.EulerType.XYZ
	EULER_SPIDER = Transform3D.EulerType.SPIDER
	ss=dict()
	ss["phi"]=currentparams[0]
	ss["theta"]=currentparams[1]
	ss["psi"]=currentparams[2]
	Rss=Transform3D(EULER_SPIDER,ss)
	vv=Rss.get_rotation(EULER_XYZ)
	params=5*[0.0]
	params[0]=vv["xtilt"]
	params[1]=vv["ytilt"]
	params[2]=vv["ztilt"]
	params[3]=currentparams[3]
	params[4]=currentparams[4]
	#print  params
	data=[]
	volft,kb=prep_vol(volref)
	data.insert(0,volft)
	data.insert(1,kb)
	data.insert(2,image)
	data.insert(3,mask)
	#print  eqproj_xyz(params,data)
	#return amoeba(currentparams, [1.0,1.0,1.0,0.5,0.5],eqproj,1.e-4,1.e-4,500,data)
	args=amoeba(params, [4.0,4.0,4.0,1.0,1.0],eqproj_xyz,1.e-4,1.e-4,500,data)
	dict_xyz = dict()
	dict_xyz["xtilt"]=args[0][0]
	dict_xyz["ytilt"]=args[0][1]
	dict_xyz["ztilt"]=args[0][2]
	Rxyz=Transform3D(EULER_XYZ,dict_xyz)
	vv=Rxyz.get_rotation(EULER_SPIDER)
	#print  vv
	return  args

def ref_3d_ali_spin(image,mask,volref,currentparams):
    from projection import prep_vol
    from utilities import amoeba
    #print  currentparams
    EULER_SPIN=Transform3D.EulerType.SPIN
    EULER_SPIDER = Transform3D.EulerType.SPIDER
    ss=dict()
    ss["phi"]   = currentparams[0]
    ss["theta"] = currentparams[1]
    ss["psi"]   = currentparams[2]
    Rss=Transform3D(EULER_SPIDER,ss)
    vv=Rss.get_rotation(EULER_SPIN)
    #print  vv
    params=5*[0.0]
    from math import acos,pi
    thetan=acos(vv["n3"])*180.0/pi
    sinn=sin(thetan*pi/180.0)
    phin=acos(vv["n1"]/sinn)*180.0/pi
    params[0]=vv["Omega"]
    params[1]=thetan  #theta
    params[2]=phin  #phi
    params[3]=currentparams[3]
    params[4]=currentparams[4]
    #print  params


    dict_spin = dict()
    dict_spin["Omega"]=params[0]
    dict_spin["n1"]=sin(params[1]*pi/180.)*cos(params[2]*pi/180.)
    dict_spin["n2"]=sin(params[1]*pi/180.)*sin(params[2]*pi/180.)
    dict_spin["n3"]=cos(params[1]*pi/180.)
    Rspin=Transform3D(EULER_SPIN,dict_spin)
    ch=Rspin.get_rotation(EULER_SPIDER)
    #print  ch

    data=[]
    volft,kb=prep_vol(volref)
    data.insert(0,volft)
    data.insert(1,kb)
    data.insert(2,image)
    data.insert(3,mask)
    #print  eqproj_spin(params,data)
    #return amoeba(currentparams, [1.0,1.0,1.0,0.5,0.5],eqproj,1.e-4,1.e-4,500,data)
    args=amoeba(params, [4.0,4.0,4.0,1.0,1.0],eqproj_spin,1.e-4,1.e-4,500,data)
    #print  args
    dict_spin = dict()
    dict_spin["Omega"]=args[0][0]
    dict_spin["n1"]=sin(args[0][1]*pi/180.)*cos(args[0][2]*pi/180.)
    dict_spin["n2"]=sin(args[0][1]*pi/180.)*sin(args[0][2]*pi/180.)
    dict_spin["n3"]=cos(args[0][1]*pi/180.)
    Rspin=Transform3D(EULER_SPIN,dict_spin)
    vv=Rspin.get_rotation(EULER_SPIDER)
    params[0]=vv["phi"]
    params[1]=vv["theta"]
    params[2]=vv["psi"]
    params[3]=args[0][3]
    params[4]=args[0][4]
    #print  vv
    return  args  #,params


def rot_func(args,data):
	
	from utilities import dropImage,info

	'''The shift(float value) is divided into translational movement and an integer shift, dx & sx_ respectively'''
	sx_ = int(args[3]);sy_ = int(args[4]);sz_ = int(args[4]); #integer shift
	dx = args[3]-sx_;dy = args[4]-sy_;dz = args[5]-sz_;       #decimal shift/translational motion
	'''----------------------------------------------'''
	x=data[0].copy()
	x.rotate_translate(args[0],args[1],args[2],dx,dy,dz)
	#data[0]=x.copy()
	#data[0].rotate(args[0],args[1],args[2])
	print data[0].get_xsize(),data[0].get_ysize(),data[0].get_zsize(),sx_,sy_,sz_,args[0],args[1],args[2]
	temp_ref_image = Util.window(data[1],data[0].get_xsize(),data[0].get_ysize(),data[0].get_zsize(),sx_,sy_,sz_)
	rot_shift3D(image_in, phi, theta=0, psi=0, sx=0, sy=0,sz=0, scale=1, method='linear')
	res = -x.cmp("SqEuclidean",temp_ref_image,{"mask":data[2]})
	print res
	info(temp_ref_image)
	info(data[0])
	dropImage(x,"out.tfc")
	del temp_ref_image
	return res

def rot_align_func(inp_image,ref_image,mask_image,az,alt,phi,sx,sy,sz):

	from utilities import amoeba

	args=[az,alt,phi,sx,sy,sz]
	scale = [1.349, -0.349, 1.349, 1.1, -1.1, 1.1]
	data=[inp_image,ref_image,mask_image]
	result=amoeba(args, scale, rot_func, 1.e-4, 1.e-4, 500 ,data)
	print result
	#info(result[1])
	del data[:],args[:],scale[:]
	return result

"""
#  written in C
def enerp(ave, numr):
	'''
		Squared norm of FTs of rings
	'''
	from math import pi
	#from utilities  import printCol
	#print  "  ENER "
	#printCol(ave)
	pi2 = pi*2
	nring = len(numr)/3
	maxrin = numr[len(numr)-1]
	ener = 0.0
	#print  numr
	for i in xrange(nring):
		numr3i = numr[2+i*3]
		np = numr[1+i*3]-1
		tq = 2*pi*numr[i*3]/numr3i
		en = tq*(ave[np]**2+ave[np+1]**2)*0.5
		for j in xrange(np+2, np+numr3i-1):  en += tq*ave[j]**2
		ener += en/numr3i
	#print  ener, ave.cmp("dot", ave, {"negative":0})
	return  ener
"""


'''
def proj_ali_old(volref, mask3D, projdata, first_ring, last_ring, rstep, xrng, yrng, step, dtheta, ref_a):
	from utilities import even_angles, info
	from projection import prgs
	from fundamentals import prepg
	from statistics import ttime
	print  ttime()
	mode="F"
	# generate list of Eulerian angles for reference projections
	#  phi, theta, psi
	ref_angles = even_angles(dtheta,0,90,0,359.99,ref_a)  # add symmetries - PHIL
	num_ref=len(ref_angles)
	# generate reference projections in polar coords
	#  begin from applying the mask, i.e., subtract the average under the mask and multiply by the mask
	if(mask3D):
		[mean, sigma, xmin, xmax, nx, ny, nz ] =  info(volref,mask3D)
		volref=(volref-mean)*mask3D

	nx=volref.get_xsize()
	ny=volref.get_ysize()
	#  center is in SPIDER convention
	cnx = int(nx/2)+1
	cny = int(ny/2)+1
	#precalculate rings
	numr=Numrinit(first_ring, last_ring, rstep, mode)
	wr=ringwe(numr ,mode)
	# K-B
	kb=kbt(nx)
	# prepare the reference volume
	volrefft = prep_vol_kb(volref,kb)
	print  ttime()

	ref_proj_rings = []     # list of (image objects) reference projections in Fourier representation
	# loop over reference angles
	for i in xrange(num_ref):
		params = [ref_angles[i][0],ref_angles[i][1],ref_angles[i][2],0.0,0.0]
		#print  params
		prjref = prgs(volrefft, kb, params)
		#info(prjref)
		temp = prepg(prjref, kb)
		cimage=Util.Polar2Dmi(temp, cnx, cny, numr, mode, kb)
		#cimage=Util.Polar2Dm(prjref,cnx,cny,numr,mode)
		Util.Frngs(cimage, numr)
		Applyws(cimage, numr, wr)
		ref_proj_rings.insert(i,cimage)
		#info(ref_proj_rings[i])
	 
	exptimage = EMData()
	#  find out how many images there are in the stack
	nprojdata = EMUtil.get_image_count(projdata)
	for imn in xrange(nprojdata):
		print  imn, ttime()
		exptimage.read_image(projdata, imn)
		pg = prepg(exptimage, kb)
		#phi1 = exptimage.get_attr('phi')
		#theta1 = exptimage.get_attr('theta')
		#psi1 = exptimage.get_attr('psi')
		sxo = exptimage.get_attr('sx')
		syo = exptimage.get_attr('sy')
		peak = -1.0E23
		for i in xrange(num_ref):
			#print  "REFERENCE IMAGE:  ",i,"  ",ttime()
			#info(ref_proj_rings[i])
			[angt,sxst,syst,mirrort,peakt]=ormqip(pg,ref_proj_rings[i],xrng,yrng,step,mode,numr,kb,cnx-sxo,cny-syo,nx)
			#print  "RESULT:  ",i,angt,sxst,syst,mirrort,peakt
			if(peakt>peak):
				peak=peakt
				numref=i
				ang=-angt
				sxs=sxst
				sys=syst
				mirror=mirrort
		#print  imn,newangles,sxs,sys,mirror,peak
		ang = (ang+360.0)%360.0
		if  mirror:
			# The ormqip returns parameters such that the transformation is applied first, the mirror operation second.
			#  What that means is that one has to change the the Eulerian angles so they point into mirrored direction: phi+180, 180-theta, 180-psi
			print  imn," M ",ang,numref,ref_angles[numref],-sxs+sxo,-sys+syo
			exptimage.set_attr_dict({'phi':(ref_angles[numref][0]+180.0)%360.0, 'theta':180-ref_angles[numref][1], 'psi':(180+ref_angles[numref][2]-ang+360.0)%360.0, 'sx':-sxs+sxo, 'sy':-sys+syo})
		else:
			print  imn,"   ",ang,numref,ref_angles[numref],sxs+sxo,sys+syo
			exptimage.set_attr_dict({'phi':ref_angles[numref][0], 'theta':ref_angles[numref][1], 'psi':(ref_angles[numref][2]+ang+360.0)%360.0, 'sx':sxs+sxo, 'sy':sys+syo})
		exptimage.write_image(projdata, imn, EMUtil.ImageType.IMAGE_HDF, True)

	return
'''


'''
def rec3D_MPI_noCTF_index(data, index, symmetry, myid, main_node = 0):
'''
  #This function is to be called within an MPI program to do a reconstruction on a dataset kept in the memory 
  #Computes reconstruction from projections whose attribute 'group' = index...
'''
	from utilities  import model_blank, reduce_EMData_to_root, getImage,send_EMData, recv_EMData
	from random import randint

	Ttype = Transform3D.EulerType.SPIDER
	fftvol = EMData()
	weight = EMData()
	nx = data[0].get_xsize()
	rec_params = {"size":nx, "npad":4, "symmetry":symmetry, "fftvol":fftvol, "weight":weight}
	rec = Reconstructors.get( "nn4", rec_params )
	rec.setup()

	for i in xrange(len(data)):
		group = data[i].get_attr('group')
		if(group == index):
			phi   = data[i].get_attr('phi')
			theta = data[i].get_attr('theta')
			psi   = data[i].get_attr('psi')
			rec.insert_slice(data[i], Transform3D(Ttype, phi, theta, psi) )

	reduce_EMData_to_root(fftvol, myid, main_node)
	reduce_EMData_to_root(weight, myid, main_node)

	if myid == main_node:   return rec.finish()
	else:                   return model_blank(nx,nx,nx)
'''
	
def combine_ref_ali_to_trans(ref_ali, spider_trans):

	from utilities import combine_params2
	"""
		Serve for ali3d_e
	"""
	res=[]
	new_angle=[ref_ali[2],ref_ali[1],ref_ali[0]]
	res.append(new_angles)
	new_spider_trans=combine_params2(spider_trans,ref_ali[3:6])
	res.append(new_spider_trans)	
	return res
	
'''  Not used anywhere
def Damerau_Levenshtein_Distance(str1, str2):
	"""
	December 11th 2006
	    computes the edit distance
	     which includes deletion, insertion, substitution
		as well as transposition
	"""
	lenStr1 = len(str1);
	lenStr2 = len(str2);
	
	d=[[0 for j in range(lenStr2)] for i in range(lenStr1) ];
	
	for i in range(lenStr1):
		for j in range(lenStr2):
			cost=1;   
			if (str1[i]==str2[j]) :
				cost=0;       # deletion, insertion, substitution
			d[i][j] = min( d[i-1][j]+1 , d[i][j-1]+1 , d[i-1][ j-1] + cost);
	
			if (i>0)&(j>0)&(str1[i]==str2[j-1])& (str1[i-1]==str2[j]):
				d[i][j] = min( d[i][j] , d[i-2][ j-2] + cost); # transposition
	return d[lenStr1-1][lenStr2-1]
'''
'''
def randperm(n):
	"""
	December 11th 2006
	    computes a random permutation of 1 through n
		This was very naive, rewritten by PAP
		WARNING - the list returned in (1 ... n)!
		doesn't seem to be used anywhere, so I commented it out PAP.
	"""
	from random import seed, randint
	seed()
	
	assigned = range(1, n+1) ; # the assignments
	for i in xrange(n):
		k = randint(0, n-1)
		t = assigned[i]
		assigned[i] = assigned[k]
		assigned[k] = t

	return assigned
'''
'''
###########-------------------------------------------------------------------------------------------------###########
#### SPIDER 3D reconstruction related parameters conversion functions   ###
def copy_trans_angles_s(transtr,ptlstr,angstr,defo_fname,stack,Pixel_size,voltage,cs=2,ctf_mul=1,symmetry="c1",deci=1,verify=1,m_radius=0,amp_contrast=.1):
	"""
	1. This command reads output parameters from a SPIDER generated 3D reconstruction, copy all 2D images 
	  (classified in defocus groups) into one hdf stack file, and store the 3D alignment paramters in the headers. The 
	   related headers are all itemized in par_str.   
	2. The program assumes that in the SPIDER 3D reconstruction directory there is a defocus doc file which includes all defoci value of all data
	   sets.
	3. The verification will perform 3D reconstrcutions of a. all particles; b. even number particls; c. odd number particles, and calculate
	   Fourier ring correlation function between volumes created by odd and even number particles.
	4. The user is surpposed to have sufficent experience about performing SPIDER 3D reconstruction and its data structure.	
	"""
	from filt import filt_params,filt_ctf,filt_btwl
	from reconstruction import recons3d_4nn_ctf
	from utilities import read_txt_col,parse_spider_fname,set_arb_params,model_circle,info
	par_str=["psi","theta","phi","sx","sy", "mirror","active","ctf_applied","defocus", "amp_contrast", "voltage", "Cs", "Pixel_size","defgrp"] 
	
	data=read_txt_col(defo_fname,"s")
	img=EMData()
	ptl_defgrp=[]
	snr=1. 
	sign=1.
	n_ptl=-1
	total=0
	angles=[]
	for igrp in xrange(len(data)):
		ftran=parse_spider_fname(transtr,igrp+1)
		fang=parse_spider_fname(angstr,igrp+1)
		ptl_stack=parse_spider_fname(ptlstr,igrp+1)
		trans=read_txt_col(ftran,"s")
		angles=read_txt_col(fang,"s")
		nima = EMUtil.get_image_count(ptl_stack)
		ptl_defgrp.append(nima)
		total+=nima
		for im in xrange(nima):	
			params=[trans[im][2],angles[im][3],angles[im][4],-trans[im][3],-trans[im][4],trans[im][5],1,ctf_mul,data[igrp][2],amp_contrast,voltage,cs,Pixel_size,igrp]		
			n_ptl+=1
			img.read_image(ptl_stack, im)
			if(ctf_mul==1): img=filt_ctf(img,data[igrp][2],cs,voltage,Pixel_size,amp_contrast)
			if(deci>1):
				lowf=.5/deci-.05
				highf=.5/deci+.05
				img=filt_btwl(img,lowf,highf)
				img=Util.decimate(img,deci,deci)
			set_arb_params(img,params,par_str)
			img.write_image(stack,n_ptl)
	m_radius=0
	if(verify==1): get_3Dfsc_stack(stack,m_radius,sign=1,snr=1,symmetry="c1")	

def copy_trans_angles_a(par_list,sp_stack,hdf_stack,new_dim,voltage,Pixel_size,ctf_mul,amp_contrast=.1,cs=2,deci=1,verify=1,symmetry="c1",m_radius=0,fmat="a",skip="C"):
	"""
		1. Read 3D reconstruction parameters from one arbitary format text file
		and store them as headers in one stack hdf file. 
		2. The parameter text file records the parameters with such sequential order:
			psi,theta,phi,sx,sy,defocus1, defocus2 
	"""
	from utilities import read_txt_col,set_arb_params,shift,window2d
	from filt import fshift,filt_ctf
	
	data=read_txt_col(par_list,fmat,skip)
	defocus=[]
	angles=[]
	shift=[]
	par_str=["psi","theta","phi","sx","sy","active","ctf_applied","defocus", "amp_contrast", "voltage", "Cs", "Pixel_size"]
	for i in xrange(len(data)):
		angles.append(data[i][1:4])
		shift.append(data[i][4:6])
		xval=(data[i][8]+data[i][9])/2.
		defocus.append(xval)
	img=EMData()
	for i in xrange(len(data)):
		img.read_image(sp_stack,i)
		if(ctf_mul>0): img=filt_ctf(img,defocus[i],cs,voltage,Pixel_size,wgh)
		img=fshift(img,-shift[i][0],-shift[i][1])
		if(deci>1): 
			lowf=.5/deci-.05
			highf=.5/deci+.05
			img=filt_btwl(img,lowf,highf)
			img=Util.decimate(img,deci,deci)
		if(new_dim>0): img=window2d(img,int(new_dim),int(new_dim))
		params=[angles[i][0],angles[i][1],angles[i][2],0,0,1,ctf_mul,defocus[i],amp_contrast,voltage,cs,Pixel_size] # normal order
		set_arb_params(img,params,par_str)
		img.write_image(hdf_stack,i)
	sign=1
	snr=1
	if(verify==1): get_3Dfsc_stack(hdf_stack,m_radius,sign,snr,symmetry)

def get_3Dfsc_stack(stack,m_radius=0,sign=1,snr=1,symmetry="c1",dres="fsc001",fval="val.spi",fvol="vol.spi",fvole="vole.spi",fvolo="volo.spi"):
	"""
		Calculate 3D vlomes from a stack file, and calculate the 
		Fourier ring correlation curve
	"""
	from filt import filt_params,filt_ctf,filt_btwl
	from reconstruction import recons3d_4nn_ctf
	from utilities import model_circle,info
	
	total=EMUtil.get_image_count(stack)
	list_p=[]
	for i in xrange(total):						 
		list_p.append(i)
	print "start reconstruction"						 
	val=recons3d_4nn_ctf(stack,list_p, snr, sign, symmetry)
	dropImage(val,"val.spi")
	print "finished"
	plist=[]
	for i in xrange(0,total,2):
		plist.append(i) 
	vole=recons3d_4nn_ctf(stack, plist, snr, sign, symmetry)		 
	dropImage(vole,"vole.spi")
	print "even finished"
	del plist
	plist=[]
	for i in xrange(1,total,2):
		plist.append(i) 
	volo=recons3d_4nn_ctf(stack, plist, snr, sign, symmetry)		 
	dropImage(volo,"volo.spi")
	print "odd finished"
	nx=vole.get_xsize()
	if(m_radius<=1): m_radius=int(nx/2)-10
	mask=model_circle(m_radius, nx, nx, nx)
	s=info(vole,mask)
	vole-=s[0]
	s=info(volo)
	volo-=s[0]
	vole*=mask
	volo*=mask
	res=fsc(volo,vole,1,"fsc001")
	fl, fh = filt_params(res)
	vol=filt_btwl(val,fl,fh)
	dropImage(vol,"vol.spi")
##############

'''


" From statistics "
def memory(since=0.0):
	'''Return memory usage in bytes.
	'''
	return _VmB('VmSize:') - since

def resident(since=0.0):
	'''Return resident memory usage in bytes.
	'''
	return _VmB('VmRSS:') - since

def stacksize(since=0.0):
	'''Return stack size in bytes.
	'''
	return _VmB('VmStk:') - since

def var_bydef(vol_stack, vol_list, info=None):
	"""  var_bydef calculates variances from the definition
	"""
	import sys
	if(info == None): info = sys.stdout
	average = EMData()
	average.read_image( vol_stack, vol_list[0] )
	average.to_zero()
	nimg = 0
	info.write( "Calculating average:" )
	info.flush()
	for ivol in vol_list:
		curt = EMData()
		curt.read_image(vol_stack, ivol )
		Util.add_img(average, curt)
		#average += curt
		if(nimg % 50==0 ) :
			info.write( "\n" )
			info.write( " %4d " % nimg )
			info.flush()
		nimg += 1
		info.write( "." )
		info.flush( )
	info.write( "\n" )
	    
	average /= len(vol_list)

	varis = average.copy()
	varis.to_zero()

	nimg=0
	info.write( "Calculating variance:" )
	info.flush()
	for ivol in vol_list:
		curt = EMData()
		curt.read_image(vol_stack,ivol)
		Util.sub_img(curt, average)
		#curt -= average
		#curt *= curt
		#varis += curt
		Util.add_img2(varis, curt)
		if(nimg % 50==0 ) :
			info.write( "\n" )
			info.write( " %4d " % nimg )
			info.flush()
		nimg=nimg+1
		info.write( "." )
	info.flush( )
	info.write( "\n" )
	
	return varis / (len(vol_list)-1)
	

def _VmB(VmKey):
	'''Private.
	'''
	
	import os
	_proc_status = '/proc/%d/status' % os.getpid()

	_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
		  'KB': 1024.0, 'MB': 1024.0*1024.0}

	# get pseudo file  /proc/<pid>/status
	#print _scale
	try:
		t = open(_proc_status)
		v = t.read()
		t.close()
	except:
		return 0.0  # non-Linux?
	# get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
	i = v.index(VmKey)
	v = v[i:].split(None, 3)  # whitespace
	if len(v) < 3:
		return 0.0  # invalid format?
	# convert Vm value to bytes
	#print _scale[v[2]],v[2],v[1]
	return float(v[1]) * _scale[v[2]]

'''####################################################################################################
################################  K-MEANS WITH PROBABILITY OF WEIGHTS CALCULATION #####################
####################################################################################################'''
'''
def K_means_prob(images, K, mask=None, init_method="Random"):
	
	e=EMData()
	if(type(images) == str):
		flag = 1
		N = EMUtil.get_image_count(images)
		e.read_image(images,0)
	else:
		if(type(images) == list):
			flag = 0
			N = len(images)
			e = images[0].copy()
		else:
			return 'Invalid Input file format --- The input images can only be a stack file or a list of images'

	nx = e.get_xsize()
	ny = e.get_ysize()
	nz = e.get_zsize()
	size = nx*ny*nz

	e.to_zero()
	
	[Cls, p] = init_Kmeans_prob(images,N,K,e,size,mask,init_method,flag)
	
	[Cls, p] = Kmeans_step_prob(images,N,K,p,Cls,size,mask,flag)
	
	for k in xrange(K):
		out2 = open("class"+str(k),"w")
		nk=0
		lst = []
		for n in xrange(N):
			dm = p[n][k]
			fl = True
			for  k1 in xrange(K):
				if(k!=k1):
					if(dm < p[n][k1]):  fl = False
			if(fl):
				nk +=1
				lst.append(n)
		out2.write("\n%s\t%d\t%s\t%d\n" % ("Cluster no:",k,"No of Object = ",nk))
		for kk in xrange(nk):
			out2.write("\t%d" % (lst[kk]))
			if(float(kk+1)/10==int(kk+1)/10):
				out2.write("\n")
		out2.write("\n")
		out2.close()
		del  lst
	

def init_Kmeans_prob(images,N,K,e,size,mask,init_method,flag):
	
	from random import seed,randint
	class Cluster:
		def __init__(self,C):
			self.C   = C
			#self.prevC = prevC
	
	Cls = []	
	e.to_zero()
	
	no = [0]*K
	p = [[0.0]*K for n in xrange(N)]
	
	seed()
	if(init_method == "Random"):

		for k in xrange(K):
			Cls.append(Cluster(None))
			Cls[k].C = e.copy()
			
		for n in xrange(N):
			
			k = randint(0,(K-1))
			
			if(flag):
				e.read_image(images,n)
			else:
				e = images[n].copy()
			
			Cls[k].C += e
			no[k] +=1
	
	for k in xrange(K):
		Cls[k].C /= no[k]
		Cls[k].C.write_image("init_K_means_average.spi",k)

	del Cluster
	
	return [Cls, p]
	
def Kmeans_step_prob(images,N,K,p,Cls,size,mask,flag):
	from math import exp
	alpha = 0.0
	e=EMData()
	e = Cls[0].C.copy()
	e.to_zero()
	c = [e.copy() for k in xrange(K)]
	cnt=0
	d = [0]*K
	for iterat in xrange(100):
		alpha += 0.1
		change =  False
		while (change==False):
			print "Iteration Number :",cnt, alpha
			cnt+=1
			#change = False
			out = open("kmns_"+str(cnt)+"_"+str(alpha)+".txt","w")
			#out1 = open("kmns_nornorm_"+str(alpha)+"_"+str(cnt)+"_"+str(MAX)+".txt","w")
			out.write("%s\t%d\n" % ("ITERATION NUMBER IS : ",cnt))
			x1 = 0
			for n in xrange(N):
				if(flag):
					e.read_image(images,n)
				else:
					e = images[n].copy()

				sumd = 0.0
				for k in xrange(K):
					if(mask==None):
						dist2 = e.cmp("SqEuclidean",Cls[k].C)
					else:
						dist2 = e.cmp("SqEuclidean",Cls[k].C,{"mask":mask})
					d[k] = exp(-alpha*dist2)				
					sumd += d[k]

				for k in xrange(K): p[n][k] = d[k]/sumd
				#out1.write("%f\t" % (p[n][k]))
				#out1.write("\n")

				#for  likmn  in xrange(MAX):
				#	sump = 0.0
				#	for k in xrange(K):
				#		p[n][k] = pow(p[n][k],alpha)
				#		sump += p[n][k]
				#	for k in xrange(K): p[n][k] /= sump

				for k in xrange(K): out.write("%f\t" % (p[n][k]))
				out.write("\n")
			for k in xrange(K): c[k] = Cls[k].C.copy()

			Cls = centroid_prob(images,N,K,Cls,p,mask,flag)
			change = True
			for k in xrange(K):
				dot = Cls[k].C.cmp("dot", c[k], {"normalize":1,"negative":0})
				if(dot < 0.999): change = False

			print "ITERATION " ,alpha,cnt,change

			for k in xrange(K): Cls[k].C.write_image("K_means_average_"+str(cnt)+"_"+str(alpha)+".spi",k)
			#out1.close()
			out.close()
			#alpha += 0.05
			
	return [Cls,p]


def centroid_prob(images,N,K,Cls,p,mask,flag):
	
	from utilities import ttime
	print ttime()
	e=EMData()
	for k in xrange(K): Cls[k].C.to_zero()

	sumw = [0.0]*K
	for n in xrange(N):
		if(flag):
			e.read_image(images,n)
		else:
			e = images[n].copy()
		
		for k in xrange(K):
			Cls[k].C = Util.madn_scalar(e, Cls[k].C, p[n][k])
			sumw[k] += p[n][k]
	for k in xrange(K): Cls[k].C /= sumw[k]
	print ttime()
		
	return Cls
#######################################################################################################################
'''


def create_write_gridprojections(volume, filepattern, anglelist,
				     kb_K=6, kb_alpha=1.75,
				     start=1, npad=2, dofakealign=False,
				     noise_sigma=0.0):
	"""Given a volume, a set of projection angles, and Kaiser-Bessel
	   window parameters, use gridding to generate projections along
	   the various angles and write them out to disk using the passed-in
	   filepattern.

	   Usage:
	     anglist = voea(60.)
	     vol = getImage("model.tcp")
	     kb_K = 6
	     kb_alpha = 1.75
	     create_write_gridprojections(vol,"prj{***}.tcp",anglist,kb_K,kb_alpha)
	"""
	from utilities import parse_spider_fname, model_gauss_noise
	from fundmentals import grotshift2d
	myparams = {"angletype":"SPIDER",
		    "anglelist":anglelist,
		    "kb_alpha":kb_alpha,
		    "kb_K":kb_K,
		    "npad":npad}
	projvol = volume.project("fourier_gridding",myparams)
	nangles = len(anglelist) / 3
	nx = volume.get_xsize()
	ny = volume.get_ysize()
	m = volume.get_xsize()
	n = npad*m
	kb = Util.KaiserBessel(kb_alpha, kb_K, m/2, kb_K/(2.*n),n)
	for i in xrange(nangles):
		if projvol.get_zsize() > 1:
			# extract the i'th z-plane
			proj = projvol.get_clip(Region(0,0,i,nx,ny,1))
		else:
			proj = projvol
		if noise_sigma > 0.0:
			proj += model_gauss_noise(noise_sigma, m, m)
		if dofakealign:
			# Randomly rotate and translate forward and back
			# to simulate an alignment
			from random import uniform
			from math import pi
			angle = uniform(0,2*pi)
			dx = uniform(0,10.)
			dy = uniform(0,10.)
			p2 = grotshift2d(proj, angle, kb, npad, dx, dy)
			p2parback = grotshift2d(p2, 0., kb, npad, -dx, -dy)
			p2back = grotshift2d(p2parback, -angle, kb, npad, 0., 0.)
			proj = p2back
		projname = parse_spider_fname(filepattern, i+start)
		proj.write_image(projname, 0, EMUtil.ImageType.IMAGE_SINGLE_SPIDER)

'''  From project '''
"""
def cre(volume, filepattern, anglelist,
				 kb_K=6, kb_alpha=1.75,
				 start=1, npad=2, dofakealign=False,
				 noise_sigma=0.0):
#    Given a volume, a set of projection angles, and Kaiser-Bessel
#       window parameters, use gridding to generate projections along
#       the various angles and write them out to disk using the passed-in
#       filepattern.
#
#       Usage:
#         anglist = voea(60.)
#         vol = getImage("model.tcp")
#         kb_K = 6
#         kb_alpha = 1.75
#         create_write_gridprojections(vol,"prj{***}.tcp",anglist,kb_K,kb_alpha)
#
    myparams = {"angletype":"SPIDER",
		"anglelist":anglelist,
		"kb_alpha":kb_alpha,
		"kb_K":kb_K,
		"npad":npad}
    #proj = volume.project("fourier_gridding",myparams)
    #projname = parse_spider_fname(filepattern, start)
    #proj.write_image(projname, 0, EMUtil.ImageType.IMAGE_SINGLE_SPIDER)
    " This does not work in C code, DO NOT USE!"
    return volume.project("fourier_gridding",myparams)
"""

'''

def pw2_adjustment(vol_in, vol_model, fscdoc, q, shell_of_noise = 20, cut_off_fsc = .2, save_curves = False):
	"""
		Enforce power spectrum of a 3D volume to that of corresponding 
		X-ray structure. The adjustment is equivalent to applying a 
		band_pass filter to the volume.
	"""
	import os
	import types
	from utilities import getImage, read_text_file
	from fundamentals import rops_table
	from filter import filt_table
	if type(vol_in) is types.StringType : vol_to_be_corrected = get_im( vol_in )
	else :                                vol_to_be_corrected = vol_in
	nx    = vol_to_be_corrected.get_xsize()
	r1    = nx//2 - 1 - shell_of_noise
	r2    = nx//2 - 1
	m1    = model_circle(r1, nx, nx, nx)
	m1   -= 1.
	m1   *=-1.
	m2    = model_circle(r2, nx, nx, nx)
	m_t   = m1*m2
	tmp_l = info(m_t)
	from utilities import gauss_edge
	mask  = gauss_edge(m_t)
	vol_n = vol_to_be_corrected*mask
	t = info(vol_n)
	vol_n -= t[0]
	t = info(vol_to_be_corrected)
	vol_to_be_corrected -= t[0]
	p3o   = rops_table(vol_to_be_corrected)
	p3b   = rops_table(vol_n)
	for i in xrange(len(p3b)): p3b[i] /= tmp_l[0]
	if type(vol_model) is types.StringType : vol_model = get_im( vol_model )
	pu    = rops_table(vol_model)
	fsc   = read_text_file(fscdoc, 1)
	p_n   = []
	out = Util.pw_extract(p3b[1:], 3, 3)
	p_n.append(0.)
	for i in xrange(1,len(p3b)):
		j = i*2
		p_n.append(out[j])
	tmp_snr = []
	eps   = 0.882
	a     = 10.624
	for j in xrange(len(fsc)):
		if fsc[j] < cut_off_fsc:
			lowf  = float(j)/len(fsc)/2.
			break
	highf = lowf+.05
	order=2.*log(eps/sqrt(a**2-1))/log(lowf/highf)
	rad   = lowf/eps**(2./order)
	H     = []	       
	for j in xrange(1,len(fsc)):
		if fsc[j] < cut_off_fsc  and fsc[j] > 0. :
			freq = float(j)/len(fsc)/2.
			snr = 1./sqrt(1.+(freq/rad)**order)
		elif fsc[j] <= 0.:               snr = 0.0 
		else:                            snr = fsc[j]/(fsc[j]+1.)
		tmp_snr.append(snr)
		tmpx = (p3o[j]-(q**2*p3b[j]+p_n[j]*(1.-q**2)))
		if    tmpx < 0. and float(j)/len(fsc) < highf : ERROR("q is too large", "pw2_adjustment")
		elif  tmpx < 0. : H.append(0.0)
		else:
			x0   = pu[j]**.5*snr
			x1   = tmpx**.5
			H.append(x0/x1)
	out_vol = filt_table(vol_to_be_corrected, H)
	if save_curves :
		from fundamentals import rops_textfile
		rops_textfile(out_vol,  "roo_adjusted.txt")
		rops_textfile(vol_model,"roo_model.txt")
		rops_textfile(vol_to_be_corrected,"roo_original.txt")
		dropSpiderDoc("snr.txt", tmp_snr)
		dropSpiderDoc("H.txt", H)
		dropSpiderDoc("bg.txt",p_n )
		dropSpiderDoc("roo_noise.txt",p3b)
		dropSpiderDoc("roo_original.txt",p3o)
		dropImage(out_vol,"vol_adjusted.spi", "s")
		dropImage(mask,"vol_mask.spi", "s")
	return  out_vol
'''


'''  From fundamentals  '''
	
def fpol_stack(stack, stack_copy, nnx, nny=0, nnz=1, RetReal = True):
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	imao = EMData()
	for im in xrange(nima):
		ima.read_image(stack,im)
		imao=ima.FourInterpol(nnx, nny, nnz, RetReal)
		imao.write_image(stack_copy, im)

def select_stack(stack, select_stack):
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack,0)
	nclass = ima.get_attr('nclass')
	class2 = []
	for im in xrange(nima):
		ima.read_image(stack,im)
		n = ima.get_attr('assign')
		if n not in class2:
			class2.append(n)		
			ima.write_image(select_stack, n)
				
def rot_shift(image, RA, method='quadrilinear'):
	return image.rot_scale_trans(RA)

'''
def rtsh(image, angle, sx=0., sy=0.):
	m=image.get_xsize()
	# padd two times
	npad=2
	n=m*npad
	# support of the window
	k=6
	alpha=1.75
	kb = Util.KaiserBessel(alpha, k, m/2, k/(2.*n), n)
	return grotshift2d(image, angle, kb, npad, sx, sy)
'''

###############################################################################################
# draft ali2d_rac_MPI
###############################################################################################

def ali2d_rac_MPI(stack, maskfile = None, kmeans = 'None', ir = 1, ou = -1, rs = 1, nclass = 2, maxit = 10, maxin = 10, check_mirror = False, rand_seed = 10):
	from global_def import MPI
	from utilities  import bcast_EMData_to_all, reduce_EMData_to_root, bcast_number_to_all
	from utilities  import send_EMData, recv_EMData
	from utilities  import model_circle, combine_params2
	from utilities  import get_arb_params, set_arb_params
	from statistics import MPIlogfile_init, MPIlogfile_print, MPIlogfile_end
	from statistics import kmnr, kmn
	from random     import randint, seed, shuffle
	from alignment  import Numrinit, ringwe, ang_n
	from copy       import deepcopy
	import time
	import sys
	from mpi 	  import mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	from mpi 	  import mpi_reduce, mpi_bcast, mpi_barrier, mpi_recv, mpi_send
	from mpi 	  import MPI_SUM, MPI_FLOAT, MPI_INT, MPI_LOR

	# [id]   part of code different for each node
	# [sync] synchronise each node
	# [main] part of code just for the main node
	# [all]  code write for all node

	# debug mode
	DEBUG = False
	K_th  = 1

	# To work
	if kmeans == 'None':
		start_k = False
	else:
		start_k = True
	
	# ------------------- MPI init ----------------------------- #
	# init
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid           = mpi_comm_rank(MPI_COMM_WORLD)

	# chose a random node as a main one
	main_node = 0
	if myid  == 0:	main_node = randint(0,number_of_proc-1)
	main_node = bcast_number_to_all(main_node,0)
	mpi_barrier(MPI_COMM_WORLD)

	if number_of_proc > nclass:
		if myid == main_node:
			print 'need number of cpus > K'
		return	
		
	t_start = time.time()
	
	# ---------------------------------------------------------- #
	
	seed(rand_seed)
	first_ring=int(ir); last_ring=int(ou); rstep=int(rs); K=int(nclass); max_iter=int(maxit); max_internal=int(maxin);
	nima = EMUtil.get_image_count(stack)
	temp = EMData()
	temp.read_image(stack, 0)
	nx = temp.get_xsize()
	ny = nx

	# default value for the last ring
	if(last_ring==-1): last_ring=nx//2-2

	# somebody dedicated could write a version with option "H" for half rings that would work for ACF functions.
	mode = "F"

	# [all] data structure
	grp_asg    = [] # assignment of groups to node
	GRP        = [] # list of local groups, each group contain index images
	IM         = [] # list of local groups, each group contain images
	AVE        = [] # list of averages (for all groups)

	# [main] 
	if myid == main_node:
		# define assignment of groups to node
		grp_asg = []
		for k in xrange(K): grp_asg.append(k % 	number_of_proc)
		grp_asg.sort()

		if start_k == False:
			# randomly list of index
			tmp = range(0, nima)
			shuffle(tmp)

			list_i = []
			for n in xrange(nima): list_i.append(n % K)
			list_i.sort()

			list_index = [[] for n in xrange(K)]
			n = 0
			for i in list_i:
			    list_index[i].append(tmp[n])
			    n += 1
		else:
			# pick-up index from ave of k-means
			list_index = [[] for n in xrange(K)]
			im = EMData()
			for k in xrange(K):
				im.read_image(kmeans, k, True)
				listim = im.get_attr('members')
				for index in listim: list_index[k].append(int(index))
				if k == 0: print list_index

	## to test
	#return

	# [main] broadcast list of assignment of groups to node
	grp_asg = mpi_bcast(grp_asg, K, MPI_INT, main_node, MPI_COMM_WORLD)
	grp_asg = grp_asg.tolist()

	# [all] display infos
	MPIlogfile_init(myid)
	MPIlogfile_print(myid, '************* ali2d_rac MPI *************\n')
	MPIlogfile_print(myid, 'Input stack                          : %s\n' % stack)
	MPIlogfile_print(myid, 'Mask file                            : %s\n' % maskfile)
	MPIlogfile_print(myid, 'Inner radius                         : %i\n' % first_ring)
	MPIlogfile_print(myid, 'Outer radius                         : %i\n' % last_ring)
	MPIlogfile_print(myid, 'Ring step                            : %i\n' % rstep)
	MPIlogfile_print(myid, 'Maximum iteration                    : %i\n' % max_iter)
	MPIlogfile_print(myid, 'Maximum internal iteration           : %i\n' % max_internal)
	MPIlogfile_print(myid, 'Consider mirror                      : %s\n' % check_mirror)
	MPIlogfile_print(myid, 'Random seed                          : %i\n' % rand_seed)
	MPIlogfile_print(myid, 'Number of classes                    : %i\n' % K)
	MPIlogfile_print(myid, 'Number of images                     : %i\n' % nima)
	MPIlogfile_print(myid, 'Number of cpus                       : %i\n' % number_of_proc)
	MPIlogfile_print(myid, 'ID cpu                               : %i\n' % myid)

	nb_grp = 0
	for k in xrange(K):
		if grp_asg[k] == myid: nb_grp += 1

	MPIlogfile_print(myid, 'Number of classes in this cpu        : %i\n' % nb_grp)
	MPIlogfile_print(myid, 'Output file                          : %s\n\n' % stack)

	# [all] generate LUT group, ex global indice grp 4 5 6 -> local indice in the node 0 1 2
	# [4, 5, 6] -> [-1, -1, -1, -1, 0, 1, 2]
	lut_grp = [-1] * K
	i       = 0
	for k in xrange(K):
		if myid == grp_asg[k]:
			lut_grp[k] = i
			i += 1
	
	# [main] send list_index to each individual group
	for k in xrange(K):
		size = []
		dst  = -1
		tmp  = []

		if myid == main_node:
			if grp_asg[k] != main_node:
				size = len(list_index[k])
				mpi_send(size, 1, MPI_INT, grp_asg[k], 0, MPI_COMM_WORLD)
				mpi_send(list_index[k], size, MPI_INT, grp_asg[k], 0, MPI_COMM_WORLD)
			else:
				GRP.append(list_index[k])
		else:
			if myid == grp_asg[k]:
				size = mpi_recv(1, MPI_INT, main_node, 0, MPI_COMM_WORLD)
				tmp  = mpi_recv(size, MPI_INT, main_node, 0, MPI_COMM_WORLD)
				tmp  = tmp.tolist()
				GRP.append(tmp)

		mpi_barrier(MPI_COMM_WORLD)

	# [all] precalculate rings
	numr     = Numrinit(first_ring, last_ring, rstep, mode)
	wr       = ringwe(numr ,mode)
	lnumr    = numr[len(numr)-1]
	norm_rsd = 0
	for n in xrange(1, len(numr), 3): norm_rsd += numr[n]
	
	# [all] prepare 2-D mask for normalization
	if maskfile:
		import  types
		if(type(maskfile) is types.StringType):
			mask2D = getImage(maskfile)
		else:
			mask2D = maskfile
	else:
		mask2D = model_circle(last_ring,nx,nx)
	if(first_ring > 0):
		tave = model_circle(first_ring-1, nx, ny)
		mask2D -= tave

	#  center is in SPIDER convention
	cnx = int(nx/2) + 1
	cny = int(ny/2) + 1
	
	# [id] read images in each local groups and resample them into polar coordinates
	if DEBUG: MPIlogfile_print(myid, 'prepare images\n')
	for grp in xrange(nb_grp):
		data = []
		im   = 0
		for index in GRP[grp]:
			temp = EMData()
			temp.read_image(stack, index)
			sx = temp.get_attr('sx')
			sy = temp.get_attr('sy')
			alpha_original = temp.get_attr('alpha')
			miri = temp.get_attr('mirror')
			[mean, sigma, qn, qm] = Util.infomask(temp, mask2D, True)
			temp = (temp - mean)/sigma
			alpha_original_n,sxn,syn,mir = combine_params2(0, -sx, -sy, 0, -alpha_original,0,0,0)
			cimage = Util.Polar2Dm(temp, cnx+sxn, cny+syn, numr, mode)
			Util.Frngs(cimage, numr)
			data.append(cimage)
			data[im].set_attr_dict({'alpha':1.0, 'alpha_original':alpha_original, 'sx':sx, 'sy':sy, 'mirror': 0})

			im += 1

		IM.append(deepcopy(data))

	del temp
	del data
	del mask2D

	# use image to 0 for define a blank image (use to reset the average)
	blank = IM[0][0]
	blank.to_zero()

	# prepare the syncronize sequence (for the com between the nodes)
	sync_org = []
	sync_dst = []
	for i in xrange(number_of_proc):
		tmp = range(number_of_proc)
		sync_dst.extend(tmp)
		for j in xrange(number_of_proc):
			sync_org.append(i)

	# debug
	if DEBUG:
		flow_ctrl = [0] * nima
		flow_cnt  = 0
	
	# [id] classification
	again =  1
	it    = -1
	while again and it < (max_iter - 1):
		it += 1
	
		mpi_barrier(MPI_COMM_WORLD)

		if DEBUG:
			flow_ite = 0

			if myid == main_node:
				tg = time.time()
				print '== ITE %d ==' % it

		# [id] compute average send to main_node
		AVE = []
		for k in xrange(K): AVE.append(blank)
		
		if DEBUG:
			MPIlogfile_print(myid, 'after init AVE\n')
			if myid == main_node: t1 = time.time()
		
		for k in xrange(K):
			if myid == grp_asg[k]:
				temp    = kmnr(IM[lut_grp[k]], -1, len(GRP[lut_grp[k]]), -1, numr, wr, check_mirror, max_internal, rand_seed, myid)
				temp   /= len(GRP[lut_grp[k]])
				AVE[k]  = temp.copy()

		if DEBUG and myid == main_node: print 'time average: %d s' % (time.time() - t1)

		if DEBUG: MPIlogfile_print(myid, 'compute ave\n')

		mpi_barrier(MPI_COMM_WORLD)

		for k in xrange(K):
			if myid != main_node:
				if myid == grp_asg[k]:
					send_EMData(AVE[k], main_node, 0)
			else:
				if grp_asg[k] != main_node and grp_asg[k] != -1:
					AVE[k] = recv_EMData(grp_asg[k], 0)

			mpi_barrier(MPI_COMM_WORLD)

		if DEBUG: MPIlogfile_print(myid, 'recv average\n')

		# [main] broadcast each average to other node
		for k in xrange(K):
			tmp = AVE[k].copy()
			bcast_EMData_to_all(tmp, myid, main_node)
			AVE[k] = tmp.copy() # need to use .copy() to store the new im
			mpi_barrier(MPI_COMM_WORLD)

		if DEBUG: MPIlogfile_print(myid, 'after send AVE\n')

		# [all] compute norm for each average
		norm = []
		for k in xrange(K):
			q   = Util.ener(AVE[k], numr)
			res = Util.Crosrng_ew(AVE[k], AVE[k], numr, wr, 0)
			norm.append((2 * q) / float(res['qn']))

		# [id] info display
		MPIlogfile_print(myid, '\n___________ Iteration %d _____________%s\n' % (it + 1, time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime())))
		for k in xrange(K):
			if lut_grp[k] != -1:
				MPIlogfile_print(myid, 'objects in class %3d : %d \n' % (k, len(GRP[lut_grp[k]])))

		MPIlogfile_print(myid, '\n')

		if DEBUG and myid == main_node: t1 = time.time()
		
		# [id] classification
		list_exg = []
		list_dst = []
		again    = 0
		Je_rsd   = 0
		for ngrp in xrange(K):
			if myid == grp_asg[ngrp]:
				exg = []
				dst = []
				for index in xrange(len(GRP[lut_grp[ngrp]])):
					dmin    = 1.0e20
					old_grp = ngrp
					new_grp = -1
					for k in xrange(K):
						if grp_asg[k] != -1: # if the group k is not empty
							if (check_mirror):
								retvals = Util.Crosrng_ew(AVE[k], IM[lut_grp[ngrp]][index], numr, wr, 0)
								qn      = retvals["qn"]
								retvals = Util.Crosrng_ew(AVE[k], IM[lut_grp[ngrp]][index], numr, wr, 1)
								qm      = retvals["qn"]
								q1      = Util.ener(AVE[k], numr)
								q2      = Util.ener(IM[lut_grp[ngrp]][index], numr)
								qn      = max(qn,qm)
								qn      = q1 + q2 - (qn * norm[k])
							else:
								retvals = Util.Crosrng_ew(AVE[k], IM[lut_grp[ngrp]][index], numr, wr, 0)
								qn      = retvals["qn"]
								q1      = Util.ener(AVE[k], numr)
								q2      = Util.ener(IM[lut_grp[ngrp]][index], numr)
								qn      = q1 + q2 - (qn * norm[k])
							if(qn < dmin):
								dmin    = qn
								new_grp = k

					Je_rsd += (dmin / float(norm_rsd))
					
					if new_grp < 0:
						print  'Error in assignment of objects to averages'
						break
					
					## TO TEST
					#if ngrp    == 0: new_grp = 1
					#if new_grp == 0: new_grp = 1
				
					if old_grp != new_grp:
						again = 1
						exg.append(GRP[lut_grp[ngrp]][index])
						dst.append(new_grp)
					
				# store list exg and dst for each loc groups
				list_exg.append(exg)
				list_dst.append(dst)

		if DEBUG and myid == main_node: print 'time classification: %d s' % (time.time() - t1)

		mpi_barrier(MPI_COMM_WORLD)

		if DEBUG: MPIlogfile_print(myid, 'after classification\n')

		# [sync] gather value of criterion Je_rsd
		Je_rsd = mpi_reduce(Je_rsd, 1, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
		Je_rsd = mpi_bcast(Je_rsd, 1, MPI_FLOAT, main_node, MPI_COMM_WORLD)
		Je_rsd = Je_rsd.tolist()
		Je_rsd = Je_rsd[0]

		MPIlogfile_print(myid, 'Criterion %11.4e\n' % Je_rsd)

		# [sync] with the other node
		again = mpi_reduce(again, 1, MPI_INT, MPI_LOR, main_node, MPI_COMM_WORLD)
		again = mpi_bcast(again, 1, MPI_INT, main_node, MPI_COMM_WORLD)
		again = again.tolist()
		again = again[0]
		
		if DEBUG:
			for grp in xrange(len(list_exg)):
				for index in list_exg[grp]:
					flow_ctrl[index] += 1
			if myid == main_node: t1 = time.time()

		# COMMUNICATION
		mpi_barrier(MPI_COMM_WORLD)
		for node in xrange(number_of_proc * number_of_proc):
			# define the origin and destination node
			org_node = sync_org[node]
			dst_node = sync_dst[node]

			# define list of group inside org node and dst node
			org_grp = []
			dst_grp = []
			for k in xrange(K):
				if grp_asg[k] == org_node:
					org_grp.append(k)
				if grp_asg[k] == dst_node:
					dst_grp.append(k)

			bag           = []
			pack          = []
			pack_size     = []
			bag_im        = []
			pack_im       = []
			lst_remove    = [[] for n in xrange(len(org_grp))]
			if myid == org_node:
				# prepare data and pack
				for outgrp in dst_grp:
					bag        = []
					bag_im     = []
					for ingrp in org_grp:
						remove   = []
						size_exg = len(list_exg[lut_grp[ingrp]])
						for n in xrange(size_exg):
							if list_dst[lut_grp[ingrp]][n] == outgrp:
								index = list_exg[lut_grp[ingrp]][n]
								bag.append(index)
								pos = GRP[lut_grp[ingrp]].index(index)
								bag_im.append(IM[lut_grp[ingrp]][pos])
								remove.append(index)

						lst_remove[lut_grp[ingrp]].extend(remove)
			
					pack.extend(bag)
					pack_im.extend(bag_im)
					pack_size.append(len(bag))
						
			# first send the pack_size to all
			pack_size = mpi_bcast(pack_size, len(dst_grp), MPI_INT, org_node, MPI_COMM_WORLD)
			pack_size = pack_size.tolist()

			mpi_barrier(MPI_COMM_WORLD)

			if DEBUG:
				data_send = 0
				data_recv = 0
				data_in   = 0
			
			# send-recv
			if myid != org_node:
				pack    = []
				pack_im = []
			for n in xrange(sum(pack_size)):
				if org_node != dst_node:
					if myid == org_node:
						# send index
						mpi_send(pack[n], 1, MPI_INT, dst_node, 0, MPI_COMM_WORLD)
						# send header [alpha, sx, sy, mirror]
						head = get_arb_params(pack_im[n], ['alpha', 'alpha_original', 'sx', 'sy', 'mirror'])
						mpi_send(head, 5, MPI_FLOAT, dst_node, 0, MPI_COMM_WORLD)
						# send image
						send_EMData(pack_im[n], dst_node, 1)
						
						if DEBUG: data_send += 1
					
					if myid == dst_node:
						# recv index
						index = mpi_recv(1, MPI_INT, org_node, 0, MPI_COMM_WORLD)
						index = index.tolist()
						pack.append(index[0])
						# recv header
						head    = mpi_recv(5, MPI_FLOAT, org_node, 0, MPI_COMM_WORLD)
						head    = head.tolist()
						head[4] = int(head[4]) # mirror is integer
						# recv image
						img   = recv_EMData(org_node, 1)
						set_arb_params(img, head, ['alpha', 'alpha_original', 'sx', 'sy', 'mirror'])
						pack_im.append(img)
						
						if DEBUG: data_recv += 1
				else:
					if DEBUG: data_in += 1

				mpi_barrier(MPI_COMM_WORLD)
	
			if DEBUG:
				flow_cnt += data_send
				flow_ite += data_send
				if dst_node != org_node:
					if myid == org_node:
						MPIlogfile_print(myid, 'send data %s %d ---> %d %2s: exp [%d] int [%d]\n' % (org_grp, org_node, dst_node, str(dst_grp).ljust(50, ' '), data_send, data_in))
					if myid == dst_node:
						MPIlogfile_print(myid, 'recv data %s %d <--- %d %2s: exp [%d] int [%d]\n' % (dst_grp, dst_node, org_node, str(org_grp).ljust(50, ' '), data_recv, data_in))
				else:
					if myid == org_node:
						MPIlogfile_print(myid, 'loca data %s %d <--> %d %2s: exp [%d] int [%d]\n' % (dst_grp, dst_node, org_node, str(org_grp).ljust(50, ' '), data_recv, data_in))

			if myid == org_node:
				# remove index and images in each group
				for ingrp in org_grp:
					for index in lst_remove[lut_grp[ingrp]]:
						pos = GRP[lut_grp[ingrp]].index(index)
						trash = GRP[lut_grp[ingrp]].pop(pos)
						trash = IM[lut_grp[ingrp]].pop(pos)
						del trash
				
			if myid == dst_node:
				i = 0
				j = 0
				for ingrp in dst_grp:
					bag    = []
					bag_im = []
					for n in xrange(j, j + pack_size[i]):
						bag.append(pack[n])
						bag_im.append(pack_im[n])
						j += 1
						
					i   += 1

					# add index and images in each group
					GRP[lut_grp[ingrp]].extend(bag)
					IM[lut_grp[ingrp]].extend(bag_im)

			# [sync]
		        mpi_barrier(MPI_COMM_WORLD)

		if DEBUG and myid == main_node:
			print 'time comm: %d s' % (time.time() - t1)
			print '\n'
			print 'time iteration: %d s\n\n' % (time.time() - tg)
		
		# [sync]
		mpi_barrier(MPI_COMM_WORLD)

		if DEBUG:
			flow_ite = mpi_reduce(flow_ite, 1, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
			flow_ite = flow_ite.tolist()

		flag = True
		if flag:
			# search the groups to remove
			grp_rmv = [0] * K
			nbr_obj = [0] * K
			for k in xrange(K):
				if myid == grp_asg[k]:
					if len(GRP[lut_grp[k]]) < K_th:
						grp_rmv[k] = 1
						nbr_obj[k] = len(GRP[lut_grp[k]])

			for k in xrange(K):
				# if the group k need to removed
				if grp_rmv[k] > 0:
					if nbr_obj[k] != 0:
						MPIlogfile_print(myid, 'Warning: class %d not enough images, remove this group\n' % k)
						org_mv = k
						dst_mv = -1

						## TO TEST
						#MPIlogfile_print(myid, 'list lut_grp: %s\n' % lut_grp)
						#MPIlogfile_print(myid, 'list grp rmv: %s\n' % grp_rmv)
						
						# search if in the node there is another group to move objects
						for q in xrange(K):
							if lut_grp[q] != -1 and grp_rmv[q] == 0:
								dst_mv = q

						## TO TEST
						#MPIlogfile_print(myid, 'grp destination %d\n' % dst_mv)
								
						# move object if there is a group destination
						if dst_mv != -1:
							#MPIlogfile_print(myid, 'from %d -> %d\n' % (org_mv, dst_mv))
							GRP[lut_grp[dst_mv]].extend(GRP[lut_grp[org_mv]])
							IM[lut_grp[dst_mv]].extend(IM[lut_grp[dst_mv]])
							MPIlogfile_print(myid, 'move objects grp %d -> grp %d\n' % (org_mv, dst_mv))
					else:
						MPIlogfile_print(myid, 'Warning: class %d is empty, remove this group.\n' % k)
	
			# clean groups
			for k in xrange(K - 1, -1, -1):
				if grp_rmv[k] > 0:
					#MPIlogfile_print(myid, 'lut_grp[k] and k: %d %d\n' % (lut_grp[k], k))
					del GRP[lut_grp[k]]
					del IM[lut_grp[k]]
							
			# broadcast the grp remove
			grp_rmv = mpi_reduce(grp_rmv, K, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
			grp_rmv = mpi_bcast(grp_rmv, K, MPI_INT, main_node, MPI_COMM_WORLD)
			grp_rmv = grp_rmv.tolist()

			# new group assign node
			for k in xrange(K):
				if grp_rmv[k] > 0: grp_asg[k] = -1			

			# new list loc group assign
			lut_grp = [-1] * K
			i       = 0
			for k in xrange(K):
				if myid == grp_asg[k]:
					lut_grp[k] = i
					i += 1

			# check empty node
			kill = 0
			if len(GRP) == 0:
				print 'Error: cpu %d is empty (no group), kill all process.\n' % myid
				MPIlogfile_print(myid, 'Error: cpu %d is empty (no group), kill all process.\n' % myid)
				kill = 1
			
			mpi_barrier(MPI_COMM_WORLD)
			kill = mpi_reduce(kill, 1, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
			kill = mpi_bcast(kill, 1, MPI_INT, main_node, MPI_COMM_WORLD)
			kill = kill.tolist()
			kill = kill[0]

			if kill > 0: return

		else:
			# check empty class
			kill = 0
			for k in xrange(K):
				if myid == grp_asg[k]:
					if len(GRP[lut_grp[k]]) < 1:
						print 'Error: class %d is empty' % k
						MPIlogfile_print(myid, 'Error: class %d is empty, kill all process.\n' % k)
						kill = 1

				mpi_barrier(MPI_COMM_WORLD)
			kill = mpi_reduce(kill, 1, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
			kill = mpi_bcast(kill, 1, MPI_INT, main_node, MPI_COMM_WORLD)
			kill = kill.tolist()
			kill = kill[0]

			if kill > 0: return

	if DEBUG:
		flow_ctrl = mpi_reduce(flow_ctrl, nima, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
		flow_ctrl = flow_ctrl.tolist()

		print myid, ': flow count [%d]' % flow_cnt

		if myid == main_node:
			print '\n ############ flow control ####################\n'
			#print TXT_flow
			#print flow_ctrl
			print '\n'
			print 'sum: %d' % sum(flow_ctrl)
	
	mpi_barrier(MPI_COMM_WORLD)

	# display the number of objects in each group
	ngrp = [0] * K
	for k in xrange(K):
		if myid == grp_asg[k]: ngrp[k] = len(GRP[lut_grp[k]])
	ngrp = mpi_reduce(ngrp, K, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
	ngrp = mpi_bcast(ngrp, K, MPI_INT, main_node, MPI_COMM_WORLD)
	ngrp = ngrp.tolist()
	MPIlogfile_print(myid, '\n== Object in each Class ==\n')
	count = 0
	for k in xrange(K):
		if ngrp[k] == 0:
			MPIlogfile_print(myid, 'class %3d : %d [removed]\n' % (k, ngrp[k]))
		else:
			MPIlogfile_print(myid, 'class %3d : %d\n' % (k, ngrp[k]))
			count += 1

	MPIlogfile_print(myid, 'number of classes: %d\n' % count)
	
	MPIlogfile_print(myid, '\nPREPARE RESULTS\n')

	'''
	# update ave according the empty group
	newAVE = []
	L      = 0
	for k in xrange(K):
		if ngrp[k] != 0:
			tmp = AVE[k].copy()
			newAVE.append(tmp)
			L += 1
	K = L
	'''

	# [main] align class averages and transfer parameters to individual images
	talpha = [0] * K
	tmir   = [0] * K
	if myid == main_node:
		for k in xrange(K): AVE[k].set_attr_dict({'alpha':1.0, 'mirror':0})
		kmn(AVE, numr, wr, check_mirror, max_iter, rand_seed)
		for k in xrange(K):
			talpha[k] = ang_n(AVE[k].get_attr('alpha'), mode, lnumr)
			tmir[k]   = AVE[k].get_attr('mirror')

		del AVE
	
	# [all] broadcast talpha and tmir
	talpha = mpi_bcast(talpha, K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
	talpha = talpha.tolist()
	tmir   = mpi_bcast(tmir, K, MPI_INT, main_node, MPI_COMM_WORLD)
	tmir   = tmir.tolist()
	
	mpi_barrier(MPI_COMM_WORLD)

	#  write out the alignment parameters to headers
	del temp
	temp = EMData()

	if DEBUG and myid == main_node: t1 = time.time()

	for k in xrange(K):
		if myid == grp_asg[k]:
			for n in xrange(len(GRP[lut_grp[k]])):
				#  First combine with angle of the average
				alpha  = ang_n(IM[lut_grp[k]][n].get_attr('alpha'), mode, lnumr)
				mirror =  IM[lut_grp[k]][n].get_attr('mirror')
				alpha, tmp, it, mirror = combine_params2(alpha, 0, 0, mirror, talpha[k], 0, 0, tmir[k])
			
				#  Second combine with given alignment
				alpha_original = IM[lut_grp[k]][n].get_attr('alpha_original')
				sx    =  IM[lut_grp[k]][n].get_attr('sx')
				sy    =  IM[lut_grp[k]][n].get_attr('sy')
				alpha_original_n, sxn, syn, mir = combine_params2(0, -sx, -sy, 0, -alpha_original, 0, 0, 0)
				alphan, sxn, syn, mir           = combine_params2(0, -sxn, -syn, 0, alpha, 0, 0, mirror)
				temp.read_image(stack, GRP[lut_grp[k]][n], True)
				temp.set_attr_dict({'alpha':alphan, 'sx':sxn, 'sy':syn, 'mirror': mir, 'nclass':K, 'ref_num':k})
				temp.write_image(stack, GRP[lut_grp[k]][n], EMUtil.ImageType.IMAGE_HDF, True)

		mpi_barrier(MPI_COMM_WORLD)

	if DEBUG and myid == main_node: print 'time write header: %d s' % (time.time() - t1)

	del temp
	del IM

	MPIlogfile_print(myid, '\n Time: %d s\n' % (time.time() - t_start))
	MPIlogfile_end(myid)



###############################################################################################
## K-MEANS STABILITY ##########################################################################


'''

-- Munkres algorithm (or Hungarian algorithm) ----------------------------------


Copyright and License
=====================

Copyright (c) 2008 Brian M. Clapper

This is free software, released under the following BSD-like license:

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  1. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

  2. The end-user documentation included with the redistribution, if any,
     must include the following acknowlegement:

     This product includes software developed by Brian M. Clapper
     (bmc@clapper.org, http://www.clapper.org/bmc/). That software is
     copyright (c) 2008 Brian M. Clapper.

     Alternately, this acknowlegement may appear in the software itself, if
     and wherever such third-party acknowlegements normally appear.

THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESSED OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL BRIAN M. CLAPPER BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 


'''
import sys
class Munkres:
    """
Calculate the Munkres solution to the classical assignment problem.
See the module documentation for usage.
    """   
    def __init__(self):
        """Create a new instance"""
        self.C = None
        self.row_covered = []
        self.col_covered = []
        self.n = 0
        self.Z0_r = 0
        self.Z0_c = 0
        self.marked = None
        self.path = None

    def make_cost_matrix(profit_matrix, inversion_function):
        """
        Create a cost matrix from a profit matrix by calling
        'inversion_function' to invert each value. The inversion
        function must take one numeric argument (of any type) and return
        another numeric argument which is presumed to be the cost inverse
        of the original profit.

        This is a static method. Call it like this:

        cost_matrix = Munkres.make_cost_matrix(matrix, inversion_func)

        For example:

        cost_matrix = Munkres.make_cost_matrix(matrix, lambda x : sys.maxint - x)
        """
        cost_matrix = []
        for row in profit_matrix:
            cost_row = []
            for value in row:
                cost_row += [inversion_function(value)]
            cost_matrix += [cost_row]
        return cost_matrix

    make_cost_matrix = staticmethod(make_cost_matrix)

    def compute(self, cost_matrix):
        """
        Compute the indexes for the lowest-cost pairings between rows and
        columns in the database. Returns a list of (row, column) tuples
        that can be used to traverse the matrix.

        The matrix must be square.
        """
        self.C = self.__copy_matrix(cost_matrix)
        self.n = len(cost_matrix)
        self.row_covered = [False for i in range(self.n)]
        self.col_covered = [False for i in range(self.n)]
        self.Z0_r = 0
        self.Z0_c = 0
        self.path = self.__make_matrix(self.n * 2, 0)
        self.marked = self.__make_matrix(self.n, 0)

        done = False
        step = 1

        steps = { 1 : self.__step1,
                  2 : self.__step2,
                  3 : self.__step3,
                  4 : self.__step4,
                  5 : self.__step5,
                  6 : self.__step6 }

        while not done:
            try:
                func = steps[step]
                #print 'calling ' + str(func)
                step = func()
            except KeyError:
                done = True

        # Look for the starred columns
        results = []
        for i in range(self.n):
            for j in range(self.n):
                if self.marked[i][j] == 1:
                    results += [(i, j)]
        assert(len(results) == self.n)

        return results

    def __copy_matrix(self, matrix):
        """Return an exact copy of the supplied matrix"""
        copy = []
        for row in matrix:
            new_row = []
            for item in row:
                new_row += [item]
            copy += [new_row]
        return copy

    def __make_matrix(self, n, val):
        """Create an NxN matrix, populating it with the specific value."""
        matrix = []
        for i in range(n):
            matrix += [[val for j in range(n)]]
        return matrix

    def __step1(self):
        """
        For each row of the matrix, find the smallest element and
        subtract it from every element in its row. Go to Step 2.
        """
        C = self.C
        n = self.n
        for i in range(n):
            minval = self.C[i][0]
            # Find the minimum value for this row
            for j in range(n):
                if minval > self.C[i][j]:
                    minval = self.C[i][j]

            # Subtract that minimum from every element in the row.
            for j in range(n):
                self.C[i][j] -= minval

        return 2

    def __step2(self):
        """
        Find a zero (Z) in the resulting matrix. If there is no starred
        zero in its row or column, star Z. Repeat for each element in the
        matrix. Go to Step 3.
        """
        n = self.n
        for i in range(n):
            for j in range(n):
                if (self.C[i][j] == 0) and \
                   (not self.col_covered[j]) and \
                   (not self.row_covered[i]):
                    self.marked[i][j] = 1
                    self.col_covered[j] = True
                    self.row_covered[i] = True

        self.__clear_covers()
        return 3

    def __step3(self):
        """
        Cover each column containing a starred zero. If K columns are
        covered, the starred zeros describe a complete set of unique
        assignments. In this case, Go to DONE, otherwise, Go to Step 4.
        """
        n = self.n
        count = 0
        for i in range(n):
            for j in range(n):
                if self.marked[i][j] == 1:
                    self.col_covered[j] = True
                    count += 1

        if count >= n:
            step = 7 # done
        else:
            step = 4

        return step

    def __step4(self):
        """
        Find a noncovered zero and prime it. If there is no starred zero
        in the row containing this primed zero, Go to Step 5. Otherwise,
        cover this row and uncover the column containing the starred
        zero. Continue in this manner until there are no uncovered zeros
        left. Save the smallest uncovered value and Go to Step 6.
        """
        step = 0
        done = False
        row = -1
        col = -1
        star_col = -1
        while not done:
            (row, col) = self.__find_a_zero()
            if row < 0:
                done = True
                step = 6
            else:
                self.marked[row][col] = 2
                star_col = self.__find_star_in_row(row)
                if star_col >= 0:
                    col = star_col
                    self.row_covered[row] = True
                    self.col_covered[col] = False
                else:
                    done = True
                    self.Z0_r = row
                    self.Z0_c = col
                    step = 5

        return step

    def __step5(self):
        """
        Construct a series of alternating primed and starred zeros as
        follows. Let Z0 represent the uncovered primed zero found in Step 4.
        Let Z1 denote the starred zero in the column of Z0 (if any).
        Let Z2 denote the primed zero in the row of Z1 (there will always
        be one). Continue until the series terminates at a primed zero
        that has no starred zero in its column. Unstar each starred zero
        of the series, star each primed zero of the series, erase all
        primes and uncover every line in the matrix. Return to Step 3
        """
        count = 0
        path = self.path
        path[count][0] = self.Z0_r
        path[count][1] = self.Z0_c
        done = False
        while not done:
            row = self.__find_star_in_col(path[count][1])
            if row >= 0:
                count += 1
                path[count][0] = row
                path[count][1] = path[count-1][1]
            else:
                done = True

            if not done:
                col = self.__find_prime_in_row(path[count][0])
                count += 1
                path[count][0] = path[count-1][0]
                path[count][1] = col

        self.__convert_path(path, count)
        self.__clear_covers()
        self.__erase_primes()
        return 3

    def __step6(self):
        """
        Add the value found in Step 4 to every element of each covered
        row, and subtract it from every element of each uncovered column.
        Return to Step 4 without altering any stars, primes, or covered
        lines.
        """
        minval = self.__find_smallest()
        for i in range(self.n):
            for j in range(self.n):
                if self.row_covered[i]:
                    self.C[i][j] += minval
                if not self.col_covered[j]:
                    self.C[i][j] -= minval
        return 4

    def __find_smallest(self):
        """Find the smallest uncovered value in the matrix."""
        minval = sys.maxint
        for i in range(self.n):
            for j in range(self.n):
                if (not self.row_covered[i]) and (not self.col_covered[j]):
                    if minval > self.C[i][j]:
                        minval = self.C[i][j]
        return minval

    def __find_a_zero(self):
        """Find the first uncovered element with value 0"""
        row = -1
        col = -1
        i = 0
        n = self.n
        done = False

        while not done:
            j = 0
            while True:
                if (self.C[i][j] == 0) and \
                   (not self.row_covered[i]) and \
                   (not self.col_covered[j]):
                    row = i
                    col = j
                    done = True
                j += 1
                if j >= n:
                    break
            i += 1
            if i >= n:
                done = True

        return (row, col)

    def __find_star_in_row(self, row):
        """
        Find the first starred element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 1:
                col = j
                break

        return col

    def __find_star_in_col(self, col):
        """
        Find the first starred element in the specified row. Returns
        the row index, or -1 if no starred element was found.
        """
        row = -1
        for i in range(self.n):
            if self.marked[i][col] == 1:
                row = i
                break

        return row

    def __find_prime_in_row(self, row):
        """
        Find the first prime element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 2:
                col = j
                break

        return col

    def __convert_path(self, path, count):
        for i in range(count+1):
            if self.marked[path[i][0]][path[i][1]] == 1:
                self.marked[path[i][0]][path[i][1]] = 0
            else:
                self.marked[path[i][0]][path[i][1]] = 1

    def __clear_covers(self):
        """Clear all covered matrix cells"""
        for i in range(self.n):
            self.row_covered[i] = False
            self.col_covered[i] = False

    def __erase_primes(self):
        """Erase all prime markings"""
        for i in range(self.n):
            for j in range(self.n):
                if self.marked[i][j] == 2:
                    self.marked[i][j] = 0

# match the asignment of two partitions with hungarian algorithm
def match_clusters_asg(asg1, asg2):
	import sys
	N   = len(asg1)
	MAT = [[0] * N for i in xrange(N)]

	# prepare matrix
	for k1 in xrange(N):
		for k2 in xrange(N):
			for index in asg1[k1]:
				if index in asg2[k2]:
					MAT[k1][k2] += 1
	cost_MAT = []
	for row in MAT:
		cost_row = []
		for col in row:
			cost_row += [sys.maxint - col]
		cost_MAT += [cost_row]

	m = Munkres()
	indexes = m.compute(cost_MAT)

	list_stable = []
	list_objs   = []
	nb_tot_objs = 0
	for r, c in indexes:
		list_in  = []
		list_out = []
		for index1 in asg1[r]:
			if index1 in asg2[c]:
				list_in.append(index1)
			else:
				list_out.append(index1)

		nb_tot_objs += len(list_in)
		nb_tot_objs += len(list_out)

		list_stable.append(list_in)

	return list_stable, nb_tot_objs

# compute the hierarchical stability between different partition from k-means (only with bdb format)
def stability_h(seed_name, nb_part):
	from copy import deepcopy

	if seed_name.split(':')[0] == 'bdb':
		N = EMUtil.get_image_count(seed_name + '1_ave')
		BDB = True
	else:
		N = EMUtil.get_image_count(seed_name + '1/average.hdf')
		BDB = False

	# read all assignment
	PART = []
	for n in xrange(1, nb_part + 1):
		L = []
		if BDB:
			DB  = db_open_dict(seed_name + str(n) + '_ave')
			for i in xrange(N):
				asg = DB.get_attr(i, 'members')
				L.append(asg)
			DB.close()
		else:
			im = EMData()
			
			for i in xrange(N):
				im.read_image(seed_name + str(n) + '/average.hdf', i, True)
				asg = im.get_attr('members')
				L.append(asg)
		PART.append(L)

	resume  = open('stability_h', 'w')

	tot_gbl = 0
	for i in xrange(N): tot_gbl += len(PART[0][i])
	
	for h in xrange(0, nb_part - 1):
		print 'h', h+1
		resume.write('h %d\n' % (h + 1))
		newPART = []
		for n in xrange(1, nb_part - h):
			LIST_stb, tot_n = match_clusters_asg(PART[0], PART[n])
			newPART.append(LIST_stb)

			nb_stb = 0
			for i in xrange(N): nb_stb += len(LIST_stb[i])

			resume.write('    p1-p%d: %5d / %5d   (%6.2f %%)\n' % (n + 1, nb_stb, tot_n, (float(nb_stb) / float(tot_n)) * 100))
			print '    p1-p%d: %5d / %5d   (%6.2f %%)' % (n + 1, nb_stb, tot_n, (float(nb_stb) / float(tot_n)) * 100)

		PART = []
		PART = deepcopy(newPART)

	nb_stb = 0
	for i in xrange(N): nb_stb += len(PART[0][i])

	stability = (float(nb_stb) / float(tot_gbl)) * 100
	resume.write('\n')
	resume.write('Stable:    %5d / %5d   (%6.2f %%)\n' % (nb_stb, tot_gbl, stability))
	resume.close()

	print '\nStable:    %5d / %5d   (%6.2f %%)\n' % (nb_stb, tot_gbl, stability)

	return stability, PART[0]

# tag data according which object is stable
def stability_tag_data(tag, PART, bdbname):
	DB = db_open_dict(bdbname)
	N  = EMUtil.get_image_count(bdbname)
	for n in xrange(N): DB.set_attr(n, tag, [0])

	ct = 0
	for k in xrange(len(PART)):
		if len(PART[k]) != 0:
			for im in PART[k]: DB.set_attr(im, tag, [1, ct])
			ct += 1
		
	DB.close()

# read meta data of the stability
def stability_read_tag(tag, bdbname):
	DB    = db_open_dict(bdbname)
	N     = EMUtil.get_image_count(bdbname)
	valk  = 0
	nbstb = 0
	try:
		for n in xrange(N):
			val = DB.get_attr(n, tag)
			if val[0] == 1:
				nbstb += 1
				if val[1] > valk:
					valk = val[1]

		print 'Stability %s: %d stable objects with %d clusters' % (tag, nbstb, valk + 1)

	except:
		print 'Tag not exist!'

	DB.close()

# extract the stable or unstable data set from the main data
def stability_extract_data(tag, kind, bdbname, bdbtarget):
	DB  = db_open_dict(bdbname)
	N   = EMUtil.get_image_count(bdbname)
	OUT = db_open_dict(bdbtarget) 

	try:
		ct = 0
		for n in xrange(N):
			val = DB.get_attr(n, tag)
			if kind == 'stable' and val[0] == 1:
				im = DB[n]
				im.set_attr('kmeans_org', n)
				OUT[ct] = im
				ct += 1
			elif kind == 'unstable' and val[0] == 0:
				im = DB[n]
				im.set_attr('kmeans_org', n)
				OUT[ct] = im
				ct += 1
	except:
		print 'Tag not exist!'

	DB.close()
	OUT.close()

# extract the stable class average from the main data set for a stability tag given
def stability_extract_stb_ave(tag, bdbname, bdbtarget):
	from utilities import model_blank
	
	DB = db_open_dict(bdbname)
	N  = EMUtil.get_image_count(bdbname)

	K = 0
	for n in xrange(N):
		val = DB.get_attr(n, tag)
		if val[0] == 1:
			if val[1] > K: K = val[1]
	K += 1
	
	asg = [[] for i in xrange(K)]
	nb  = [0] * K
	bk = model_blank(DB.get_attr(0, 'nx'), DB.get_attr(0, 'ny'))
	AVE = []
	for k in xrange(K): AVE.append(bk.copy())

	for n in xrange(N):
		val = DB.get_attr(n, tag)
		if val[0] == 1:
			Util.add_img(AVE[val[1]], DB[n])
			asg[val[1]].append(n)
			nb[val[1]] += 1

	OUT = db_open_dict(bdbtarget)
	for k in xrange(K):
		Util.mul_scalar(AVE[k], 1 / float(nb[k]))
		OUT[k] = AVE[k]
		OUT.set_attr(k, 'members', asg[k])
		OUT.set_attr(k, 'nobjects', nb[k])
	OUT.close()
	DB.close()

# change ID of object in each class average to refert at the ID of the main data set
def herit_ID_from_main_data(seed_name, nb_part, bdbname_child):
	K  = EMUtil.get_image_count(seed_name + '1_ave')
	CH = db_open_dict(bdbname_child)
	
	for n in xrange(1, nb_part + 1):
		DB = db_open_dict(seed_name + str(n) + '_ave')
		for k in xrange(K):
			list_im = DB.get_attr(k, 'members')
			newlist = []
			for im in list_im: newlist.append(CH.get_attr(im, 'kmeans_org'))
			DB.set_attr(k, 'members', newlist)

	CH.close()
	DB.close()

# match two partitions with hungarian algorithm name1.hdf name2.hdf and N1 (number of images in partition)
def Match_clusters(name1, name2, N1):
    from copy import deepcopy

    MAT   = [[0]*N1 for i in xrange(N1)]
    im    = EMData()
    list1 = []
    list2 = []
    tot_n = 0
    for n in xrange(N1):
        im.read_image(name1, n, True)
        tmp = im.get_attr('members')

        if isinstance(tmp, list):
            list1.append(tmp)
        else:
            if tmp != -1:
                list1.append([tmp])
            else:
                list1.append([])

        im.read_image(name2, n, True)
        tmp = im.get_attr('members')

        if isinstance(tmp, list):
            list2.append(tmp)
        else:
            if tmp != -1:
                list2.append([tmp])
            else:
                list2.append([])
      
        tot_n += len(list1[n])

    # match class
    for k1 in xrange(N1):
        for k2 in xrange(N1):
            for index in list1[k1]:
                if index in list2[k2]:
                    MAT[k1][k2] += 1

    # sum
    sum_r = [0] * N1
    for k1 in xrange(N1):
        sum_r[k1] = sum(MAT[k1])

    sum_c = [0] * N1
    for k2 in xrange(N1):
        for k1 in xrange(N1):
            sum_c[k2] += MAT[k1][k2]

    sum_sum = sum(sum_r)
    if sum_sum != sum(sum_c):
        print 'error sum'
        exit()

    ## cost mat
    cost_MAT = []
    for row in MAT:
        cost_row = []
        for col in row:
            cost_row += [sys.maxint - col]
        cost_MAT += [cost_row]

    m = Munkres()
    indexes = m.compute(cost_MAT)

    list_stable = []
    list_objs   = []
    for r, c in indexes:
        list_in  = []
        list_out = []
        for index1 in list1[r]:
            if index1 in list2[c]:
                list_in.append(index1)
            else:
                list_out.append(index1)

        list_all = deepcopy(list_in)
        list_all.extend(list_out)
        list_all.sort()

        list_stable.append(list_in)
        list_objs.append(list_all)


    return indexes, list_stable, list_objs, tot_n


# compute the hierarchical stability between partition given by k-means only
# seed_name = 'K16_p', nb_part = 5 and org = 'data.hdf'
def h_stability(seed_name, nb_part, org):
	from utilities import get_im, model_blank
	N1  = EMUtil.get_image_count(seed_name + '1/average.hdf')
	tmp = get_im(seed_name + '1/average.hdf', 0)
	nx  = tmp.get_xsize()
	ny  = tmp.get_ysize()

	## Strategie hierarchical
	MEM = []
	resume  = open('summarize', 'w')
	tot_gbl = 0
	for h in xrange(0, nb_part - 1):
	    nb_part_cur = nb_part - h
	    print 'Hierarchical ', h
	    resume.write('Hierarchical %d:\n' % h)

	    if h == 0:
		name1 = seed_name + '1/average.hdf'
	    else:
		name1 = 'h%d_stable_1.hdf' % h

	    for n in xrange(1, nb_part_cur):
		if h == 0:
		    name2 = seed_name + str(n + 1) + '/average.hdf'
		else:
		    name2 = 'h%d_stable_%d.hdf' % (h, n + 1)

		indexes, list_stable, list_objs, tot_n = Match_clusters(name1, name2, N1)

		if h == 0: tot_gbl = tot_n

		print ' match p1 - p%d' % (n + 1)

		out = open('h%d_p1_p%d' % (h, n + 1), 'w')
		ct  = 0
		for r, c in indexes:
		    out.write('%3d %3d   %5d\n' % (r, c, len(list_stable[r])))
		    ct += len(list_stable[r])

		if ct == 0:
			print 'warning: stability 0%'
			return 0.0
		    
		out.write('\nTot: %5d / %5d     (%3.2f %%)\n' % (ct, tot_n, (float(ct) / float(tot_n)) * 100))
		out.close()

		resume.write('    p1-p%d: %5d / %5d   (%3.2f %%)\n' % (n + 1, ct, tot_n, (float(ct) / float(tot_n)) * 100))

		# prepare to intersect partition
		for k in xrange(len(list_stable)):
		    ave    = model_blank(nx, ny)
		    nim    = len(list_stable[k])
		    assign = []

		    if nim != 0:
			for i in xrange(nim):
			    im = get_im(org, int(list_stable[k][i]))
			    Util.add_img(ave, im)
			    assign.append(float(list_stable[k][i]))
			Util.mul_scalar(ave, 1 / float(nim))

		    if len(assign) == 0:
			assign.append(float(-1))

		    ave.set_attr_dict({'nobjects':nim, 'members':assign})
		    ave.write_image('h%d_stable_%d.hdf' % (h + 1, n), k)


	stability = (float(ct) / float(tot_gbl)) * 100

	resume.write('\n')
	resume.write('Stable:    %5d / %5d   (%3.2f %%)\n' % (ct, tot_gbl, stability))
	resume.close()

	print 'H stable:    %5d / %5d   (%3.2f %%)\n' % (ct, tot_gbl, stability)

	# generate data of unstable objects
	ct = 0
	stable = []
	for k in xrange(len(list_stable)): stable.extend(list_stable[k])

	f1 = open('list_unstable', 'w')
	f2 = open('list_stable',   'w')
	for n in xrange(tot_gbl):
	    if n not in stable:
		f1.write('%d\n' % n)
	    else:
		f2.write('%d\n' % n)

	f1.close()
	f2.close()

	return stability

## END K-MEANS STABILITY ######################################################################
###############################################################################################


###############################################################################################
## K-MEANS OLD HDF VERSION ####################################################################

# K-means main driver
def k_means_main(stack, out_dir, maskname, opt_method, K, rand_seed, maxit, trials, critname, CTF = False, F = 0, T0 = 0, MPI = False, SA2 = False, DEBUG = False):
	from utilities 	import print_begin_msg, print_end_msg, print_msg
	from statistics import k_means_criterion, k_means_export, k_means_open_im, k_means_headlog
	import sys

	N = EMUtil.get_image_count(stack)

	if opt_method=='cla':
		if MPI:
			from statistics import k_means_cla_MPI
			k_means_cla_MPI(stack, out_dir, maskname, K, rand_seed, maxit, trials, critname, CTF, 0, -1, -1, -1, -1, [-1], F, T0, SA2)

		else:
			N = EMUtil.get_image_count(stack)
								
			print_begin_msg('k-means')
			k_means_headlog(stack, out_dir, opt_method, N, K, critname, maskname, trials, maxit, CTF, T0, F, SA2, rand_seed, 1)

			from statistics import k_means_classical
			[Cls, assign] = k_means_classical(stack, maskname, K, rand_seed, maxit, trials, CTF, F, T0, SA2, DEBUG)
			crit          = k_means_criterion(Cls, critname)
			k_means_out_res(Cls, crit, assign, out_dir)
			
			print_end_msg('k-means')	

	elif opt_method=='SSE':
		if MPI:
			from statistics import k_means_SSE_MPI
			k_means_SSE_MPI(stack, out_dir, maskname, K, rand_seed, maxit, trials, critname, CTF, 0, -1, -1, -1, -1, [-1], F, T0, SA2)
		else:
			N = EMUtil.get_image_count(stack)
						
			print_begin_msg('k-means')
			k_means_headlog(stack, out_dir, opt_method, N, K, critname, maskname, trials, maxit, CTF, T0, F, SA2, rand_seed, 1)

			from statistics import k_means_SSE
			[Cls, assign] = k_means_SSE(stack, maskname, K, rand_seed, maxit, trials, CTF, F, T0, SA2, DEBUG)
			crit          = k_means_criterion(Cls, critname)
			k_means_out_res(Cls, crit, assign, out_dir)

			print_end_msg('k-means')	

	else:
		ERROR('Kind of k-means unknown', 'k_means_mains', 1)
			
# K-means groups driver
def k_means_groups(stack, out_file, maskname, opt_method, K1, K2, rand_seed, maxit, trials, crit, CTF, F, T0, SA2, MPI=False, DEBUG=False):
	if MPI:
		from statistics import k_means_groups_MPI
		k_means_groups_MPI(stack, out_file, maskname, opt_method, K1, K2, rand_seed, maxit, trials, crit, CTF)
		
	else:
		from statistics import k_means_groups_serial
		[rescrit, KK] = k_means_groups_serial(stack, out_file, maskname, opt_method, K1, K2, rand_seed, maxit, trials, crit, CTF)
		
		return rescrit, KK

# -- K-means logfile --------------------------------------------------------------------------

# Logfile to MPI
def MPIlogfile_init(N):
	import time
	out = open('%s_MPI_logfile' % str(N).rjust(3,'0'), 'a')
	out.write('_BEGIN__________________________________________________________\n\n')
	out.write('MPI logfile %s\n' % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()))
	out.write('Node number: %d\n' % N)
	out.close()

# LogFile to MPI
def MPIlogfile_print(N, msg):
	out = open('%s_MPI_logfile' % str(N).rjust(3,'0'), 'a')
	out.write(msg)
	out.close()
	
# LogFile to MPI
def MPIlogfile_end(N):
	import time
	out = open('%s_MPI_logfile' % str(N).rjust(3,'0'), 'a')
	out.write('\n_END_______________________%s_________\n\n\n\n\n' % time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime()))

def k_means_out_res(Cls, crit, assign, out_dir):
	import os
	
	if os.path.exists(out_dir):  os.system('rm -rf '+out_dir)
	os.mkdir(out_dir)
	
	# Write informations on results
	Je = 0
	for k in xrange(Cls['k']): Je += Cls['Ji'][k]
	os.system('rm -f '+out_dir+'/kmeans_classification_chart.txt')
	out  = open(out_dir+"/kmeans_classification_chart.txt",'w')
	out.write("\n\t%s\t%11.6e\n\n" % ("The total Sum of Squares Error (Je) = ", Je))
	
	for name in crit['name']:
		if name == 'C':
			out.write("\t%s\t%11.4e\n"%("Criteria Coleman", crit['C']))
		elif name == 'H':
			out.write("\t%s\t%11.4e\n"%("Criteria Harabasz", crit['H']))
		elif name == 'D':
			out.write("\t%s\t%11.4e\n"%("Criteria Davies-Bouldin", crit['D']))
		else:
			ERROR("Kind of criterion k-means unknown","k_means_out_res",1)	

	out.write('\n')
	for k in xrange(Cls['k']):
		# limitation of hdf file in the numbers of attributes
		if Cls['n'][k] > 16000:
			print 'WARNING: limitation of number attributes in hdf file, the results will export in separate files \n'
			outfile = open('%d_kmeans' % k, 'w')
			list_images = []
			for i in xrange(len(assign)):
				if assign[i] == k:
					list_images.append(i)
					outfile.write(str(i) +'\n')
			outfile.close()
			Cls['ave'][k].set_attr_dict({'Class_average':1.0, 'nobjects':float(Cls['n'][k])})
		else:
			lassign = []
			for i in xrange(len(assign)):
				if(assign[i] == k):  lassign.append(float(i))
			Cls['ave'][k].set_attr_dict({'Class_average':1.0, 'nobjects':float(Cls['n'][k]), 'members':lassign})

		Cls['ave'][k].set_attr_dict({'alpha':0.0, 'sx':0.0, 'sy':0.0, 'mirror':0.0})
		Cls['var'][k].set_attr_dict({'alpha':0.0, 'sx':0.0, 'sy':0.0, 'mirror':0.0})
		Cls['var'][k].set_attr_dict({'Class_variance':1.0, 'nobjects':float(Cls['n'][k])})
		Cls['ave'][k].write_image(out_dir+"/average.hdf", k)
		Cls['var'][k].write_image(out_dir+"/variance.hdf", k)
		out.write("\t%s\t%d\t%s\t%d" % ("Cluster no:",k, "No of Objects = ",Cls['n'][k]))
		if(Cls['n'][k] > 1):
			out.write("\t%s\t%11.6e\t%s\t%11.6e\n" % ("Sum of Squares Error Ji",Cls['Ji'][k]," Variance",Cls['Ji'][k]/float(Cls['n'][k]-1)))
		else:
			out.write("\t%s\t%11.6e\n" % ("Sum of Squares Error Ji",Cls['Ji'][k]))
					
	out.close()

# K-means with classical method
def k_means_classical(stack, mask, K, rand_seed, maxit, trials, CTF, F=0, T0=0, SA2=False, DEBUG=False):
	from utilities 		import model_blank, get_im
	from random    		import seed, randint
	from utilities 		import print_begin_msg, print_end_msg, print_msg
	from copy		import deepcopy
	from fundamentals       import rot_shift2D, rot_shift3D
	from sys		import exit
	import time
	if CTF:
		from morphology		import ctf_2, ctf_1d
		from filter		    import filt_ctf, filt_table
		from fundamentals 	import fftip
		from utilities		import get_arb_params

	# Simulate annealing use or not
	if F != 0: SA = True
	else:      SA = False

	if SA:
		# for simulate annealing
		from math   import exp
		from random import random

	# to bdb
	if stack.split(':')[0] == 'bdb':
		BDB   = True
		stack = stack.split(':')[1]
		DB    = EMAN2DB.open_db()
	else:
		BDB   = False


	# define parameters
	if BDB: N = EMUtil.get_image_count('bdb:' + stack)
	else:   N = EMUtil.get_image_count(stack)

	t_start = time.time()
		
	# Informations about images
	if BDB: image = get_im('bdb:' + stack, 0)
	else:   image = get_im(stack, 0)
	nx    = image.get_xsize()
	ny    = image.get_ysize()
	nz    = image.get_zsize()
	or_nx = nx
	or_nz = nz
	or_ny = ny
	buf   = model_blank(nx, ny, nz)
	if CTF:	fftip(buf)
	
	# Variables			
	if rand_seed > 0:  seed(rand_seed)
	else:              seed()
	Cls        = {}
	Cls['n']   = [0]*K   # number of objects in a given cluster
	Cls['ave'] = [0]*K   # value of cluster average
	Cls['var'] = [0]*K   # value of cluster variance
	Cls['Ji']  = [0]*K   # value of Ji
	Cls['k']   =  K	     # value of number of clusters
	Cls['N']   =  N
	assign     = [0]*N 
	im_M       = []
	
	if CTF:
		parnames    = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
		ctf	    = {}
		ctf2        = {}
		Cls_ctf2    = {}
		ctf_params  = get_arb_params(image, parnames)
		ctm         = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
		len_ctm	    = len(ctm)
			
	# Load images and init clusters
	print_msg('> Load images\n')
	
	if mask:
		import types
		if (type(mask) is types.StringType):
			mask = get_im(mask)
			
	# apply CTF if flag
	if BDB: DB.open_dict(stack)
	if CTF:
		for im in xrange(N):
			# obtain image
			if BDB: image = DB[stack][im]
			else:	image = get_im(stack, im)
		
			# apply parameters
			alpha  = image.get_attr('alpha')
			sx     = image.get_attr('sx')
			sy     = image.get_attr('sy')
			mirror = image.get_attr('mirror')
			image  = rot_shift2D(image, alpha, sx, sy, mirror)
						
			# obtain ctf
			ctf_params = get_arb_params(image, parnames)
			
			# apply ctf if flag
			if ctf_params[6]:
				ERROR("K-means cannot be performed on CTF-applied images", "k_means",1)
				return -1
			
			# store the ctf, allow limit acces file
			ctf[im]  = ctf_1d(or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			ctf2[im] = ctf_2( or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
									
			# apply mask
			if mask:	Util.mul_img(image, mask)
									
			# fft
			fftip(image)
			
			# store	image
			im_M.append(image)
			
			# update info of images
			if im == 0:
				nx   = im_M[im].get_xsize()
				ny   = im_M[im].get_ysize()
				nz   = im_M[im].get_zsize()
				
				# compute the norm
				norm = nx * ny * nz			

	else:
		for im in xrange(N):
			# obtain image
			if BDB: image = DB[stack][im]
			else:	image = get_im(stack, im)
		
			# 3D object
			if or_nz > 1:
				# apply parameters
				phi    = image.get_attr('phi')
				theta  = image.get_attr('theta')
				psi    = image.get_attr('psi')
				s3x    = image.get_attr('s3x')
				s3y    = image.get_attr('s3y')
				s3z    = image.get_attr('s3z')
				mirror = image.get_attr('mirror')
				image  = rot_shift3D(image, phi, theta, psi, s3x, s3y, s3z)
				if mirror: image.process_inplace('mirror', {'axis':'x'})
			# 2D object
			elif or_ny > 1:
				# apply parameters
				alpha  = image.get_attr('alpha')
				sx     = image.get_attr('sx')
				sy     = image.get_attr('sy')
				mirror = image.get_attr('mirror')
				image  = rot_shift2D(image, alpha, sx, sy, mirror)
								
			# apply mask
			if mask:	image = Util.compress_image_mask(image, mask)

			# update info of images
			if im == 0:
				nx   = image.get_xsize()
				ny   = image.get_ysize()
				nz   = image.get_zsize()

				# compute the norm
				norm = nx * ny * nz

				# new buf size
				buf  = model_blank(nx, ny, nz)	

			# store	image
			im_M.append(image)

	if BDB: DB.close_dict(stack)
				
	# TRIALS
	if trials > 1:
		MemCls, MemJe, MemAssign = {}, {}, {}
	else:
		trials = 1
	ntrials = 0
	while ntrials < trials:
		ntrials  += 1

		# for simulate annealing
		if SA: T = T0
		
		# Init the cluster by an image empty
		for k in xrange(K):
			Cls['ave'][k] = buf.copy()
			Cls['var'][k] = buf.copy()
			Cls['n'][k]   = 0
			Cls['Ji'][k]  = 0
		
		## Random method
		retrial = 20
		while retrial > 0:
			retrial -= 1
			i = 0
			for im in xrange(N):
				assign[im] = randint(0, K-1)
				Cls['n'][assign[im]] += 1
			
			flag, k = 1, K
			while k>0 and flag:
				k -= 1
				if Cls['n'][k] == 0:
					flag = 0
					if retrial == 0:
						ERROR("Empty class in the initialization","k_means_classical",1)
					for k in xrange(K):
						Cls['n'][k] = 0
			
			if flag == 1:	retrial = 0
		
		## Calculate averages, if CTF: ave = S CTF.F / S CTF**2
		if CTF:
			# first init ctf2
			for k in xrange(K):	Cls_ctf2[k] = [0] * len_ctm
						
			for im in xrange(N):
				# compute ctf2				
				for i in xrange(len_ctm):	Cls_ctf2[assign[im]][i] += ctf2[im][i]
				
				# compute average first step
				CTFxF = filt_table(im_M[im], ctf[im])
				Util.add_img(Cls['ave'][assign[im]], CTFxF)
						
			for k in xrange(K):
				for i in xrange(len_ctm):	Cls_ctf2[k][i] = 1.0 / float(Cls_ctf2[k][i])
				Cls['ave'][k] = filt_table(Cls['ave'][k], Cls_ctf2[k])

			# compute Ji and Je
			for n in xrange(N):
				CTFxAve               = filt_table(Cls['ave'][assign[n]], ctf[n])
				Cls['Ji'][assign[n]] += CTFxAve.cmp("SqEuclidean", im_M[n]) / norm
			Je = 0
			for k in xrange(K):        Je = Cls['Ji'][k]
																			
		else:
			# compute average
			for im in xrange(N):	Util.add_img(Cls['ave'][assign[im]], im_M[im])
			for k in xrange(K):	Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0 / float(Cls['n'][k]))

			# compute Ji and Je
			Je = 0
			for n in xrange(N):	Cls['Ji'][assign[n]] += im_M[n].cmp("SqEuclidean",Cls['ave'][assign[n]])/norm
			for k in xrange(K):	Je += Cls['Ji'][k]	
		
		## Clustering		
		ite       = 0
		watch_dog = 0
		old_Je    = 0
		change    = True

		if DEBUG: print 'init Je', Je
		
		print_msg('\n__ Trials: %2d _________________________________%s\n'%(ntrials, time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime())))
		while change and watch_dog < maxit:
			ite       += 1
			watch_dog += 1
			change     = False
			Je	   = 0
			if SA: ct_pert = 0
		
			for im in xrange(N):
		
				if CTF:
					CTFxAVE = []
					for k in xrange(K): CTFxAVE.append(filt_table(Cls['ave'][k], ctf[im]))
					res = Util.min_dist(im_M[im], CTFxAVE)
				else:
					res = Util.min_dist(im_M[im], Cls['ave'])
				
				# Simulate annealing
				if SA:
					if SA2:
						dJe = [0.0] * K
						ni  = float(Cls['n'][assign[im]])
						di  = res['dist'][assign[im]]
											
						for k in xrange(K):
							if k != assign[im]:
								nj  = float(Cls['n'][k])
								dj  = res['dist'][k]
								
								dJe[k] = -( (nj/(nj+1))*(dj/norm) - (ni/(ni-1))*(di/norm) )
															
							else:
								dJe[k] = 0

						# norm <0 [-1;0], >=0 [0;+1], if just 0 norm to 1
						nbneg  =  0
						nbpos  =  0
						minneg =  0
						maxpos =  0
						for k in xrange(K):
							if dJe[k] < 0.0:
								nbneg += 1
								if dJe[k] < minneg: minneg = dJe[k]
							else:
								nbpos += 1
								if dJe[k] > maxpos: maxpos = dJe[k]
						if nbneg != 0:                   dneg = -1.0 / minneg
						if nbpos != 0 and maxpos != 0:   dpos =  1.0 / maxpos
						for k in xrange(K):
							if dJe[k] < 0.0: dJe[k] = dJe[k] * dneg
							else:
								if maxpos != 0: dJe[k] = dJe[k] * dpos
								else:           dJe[k] = 1.0

						# q[k]
						q      = [0.0] * K
						arg    = [0.0] * K
						maxarg = 0
						for k in xrange(K):
							arg[k] = dJe[k] / T
							if arg[k] > maxarg: maxarg = arg[k]
						limarg = 17
						if maxarg > limarg:
							sumarg = float(sum(arg))
							for k in xrange(K): q[k] = exp(arg[k] * limarg / sumarg)
						else:
							for k in xrange(K): q[k] = exp(arg[k])
										
						# p[k]
						p = [[0.0, 0] for i in xrange(K)]
						sumq = float(sum(q))
						for k in xrange(K):
							p[k][0] = q[k] / sumq
							p[k][1] = k
											
						p.sort()
						c = [0.0] * K
						c[0] = p[0][0]
						for k in xrange(1, K): c[k] = c[k-1] + p[k][0]

						pb = random()
						select = -1
						for k in xrange(K):
							if c[k] > pb:
								select = p[k][1]
								break
					

						if select != res['pos']:
							ct_pert    += 1
							res['pos']  = select

						
					else:
						if exp( -(1) / float(T) ) > random():
							res['pos']  = randint(0, K - 1)
							ct_pert    += 1
								
				# update assign
				if res['pos'] != assign[im]:
					Cls['n'][assign[im]] -= 1
					if Cls['n'][assign[im]] < 1: Cls['n'][assign[im]] = 0
					assign[im]            = res['pos']
					Cls['n'][assign[im]] += 1
					change                = True

							
			# manage empty cluster
			for k in xrange(K):
				if Cls['n'][k] < 1:
					ERROR("Empty groups in kmeans_classical","k_means_classical",1)
					exit()
													
			# Update clusters
			for k in xrange(K):
				Cls['ave'][k] = buf.copy()
				Cls['Ji'][k]  = 0
				Je = 0
			
			if CTF:
				# first init ctf2
				for k in xrange(K):	Cls_ctf2[k] = [0] * len_ctm

				for im in xrange(N):
					# compute ctf2				
					for i in xrange(len_ctm):	Cls_ctf2[assign[im]][i] += ctf2[im][i]

					# compute average first step
					CTFxF = filt_table(im_M[im], ctf[im])
					Util.add_img(Cls['ave'][assign[im]], CTFxF)

				for k in xrange(K):
					for i in xrange(len_ctm):	Cls_ctf2[k][i] = 1.0 / float(Cls_ctf2[k][i])
					Cls['ave'][k] = filt_table(Cls['ave'][k], Cls_ctf2[k])

				# compute Ji and Je
				for n in xrange(N):
					CTFxAve               = filt_table(Cls['ave'][assign[n]], ctf[n])
					Cls['Ji'][assign[n]] += CTFxAve.cmp("SqEuclidean", im_M[n]) / norm
				Je = 0
				for k in xrange(K):       Je += Cls['Ji'][k]
			
			else:
				for im in xrange(N): Util.add_img(Cls['ave'][assign[im]], im_M[im])
				for k in xrange(K):  Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))

				# compute Ji and Je
				Je = 0
				for n in xrange(N):	Cls['Ji'][assign[n]] += im_M[n].cmp("SqEuclidean",Cls['ave'][assign[n]]) / norm
				for k in xrange(K):	Je += Cls['Ji'][k]	
									
				
			# threshold convergence control
			if Je != 0:
				thd = abs(Je - old_Je) / Je
			else:
				thd = 0
			if SA:
				if thd < 1e-12 and ct_pert == 0: watch_dog =maxit
			else:
				if thd < 1e-8:                   watch_dog = maxit
			old_Je = Je

			if SA:
				# Simulate annealing, update temperature
				T *= F
				if SA2:
					if T < 0.09: SA = False

				print_msg('> iteration: %5d    criterion: %11.6e    T: %13.8f  ct disturb: %5d\n' % (ite, Je, T, ct_pert))
				if DEBUG: print '> iteration: %5d    criterion: %11.6e    T: %13.8f  ct disturb: %5d' % (ite, Je, T, ct_pert)
			else:
				print_msg('> iteration: %5d    criterion: %11.6e\n' % (ite, Je))
				if DEBUG: print '> iteration: %5d    criterion: %11.6e' % (ite, Je)
						
		# memorize the result for this trial	
		if trials > 1:
			MemCls[ntrials-1]    = deepcopy(Cls)
			MemJe[ntrials-1]     = deepcopy(Je)
			MemAssign[ntrials-1] = deepcopy(assign)
						
	# if severals trials choose the best
	if trials > 1:
		val_min = 1.0e20
		best    = -1
		for n in xrange(trials):
			if MemJe[n] < val_min:
				val_min = MemJe[n]
				best    = n
		
		# affect the best
		Cls    = MemCls[best]
		Je     = MemJe[best]
		assign = MemAssign[best]		
	
	if CTF:
		# compute Ji and the variance S (F - CTF * Ave)**2
		for n in xrange(N):
			CTFxAve   	      = filt_table(Cls['ave'][assign[n]], ctf[n])	
			Cls['Ji'][assign[n]] += CTFxAve.cmp("SqEuclidean", im_M[n]) / norm
			
			buf.to_zero()
			buf = Util.subn_img(CTFxAve, im_M[n])
			Util.add_img(Cls['var'][assign[n]], buf) # **2
			
	else:
		# compute Ji
		for n in xrange(N): 	Cls['Ji'][assign[n]] += im_M[n].cmp("SqEuclidean",Cls['ave'][assign[n]]) / norm
		
		# compute the variance 1/n S(im-ave)**2 -> 1/n (Sim**2 - n ave**2)
		for im in xrange(N):	Util.add_img2(Cls['var'][assign[im]],im_M[im])
		for k in xrange(K):
			buf.to_zero()
			Util.add_img2(buf, Cls['ave'][k])
			Util.mad_scalar(Cls['var'][k], buf, -float(Cls['n'][k]))
			Util.mul_scalar(Cls['var'][k], 1.0/float(Cls['n'][k]))
						
			# Uncompress ave and var images if the mask is used
			if mask:
				Cls['ave'][k] = Util.reconstitute_image_mask(Cls['ave'][k], mask)
				Cls['var'][k] = Util.reconstitute_image_mask(Cls['var'][k], mask)
	
	# prepare the results
	if CTF:
		# ifft
		for k in xrange(K):
			fftip(Cls['ave'][k])
			fftip(Cls['var'][k])
			Cls['ave'][k].postift_depad_corner_inplace()
			Cls['var'][k].postift_depad_corner_inplace()
	
	# information display
	print_msg('\n')
	time_run = int(time.time() - t_start)
	time_h   = time_run / 3600
	time_m   = (time_run % 3600) / 60
	time_s   = (time_run % 3600) % 60
	print_msg('Time: %s h %s min %s s\n' % (str(time_h).rjust(2, '0'), str(time_m).rjust(2, '0'), str(time_s).rjust(2, '0')))
	print_msg('Criterion = %11.6e \n' % Je)
	for k in xrange(K):	print_msg('Cls[%i]: %i\n'%(k, Cls['n'][k]))
	
	# return Cls, assign
	return Cls, assign

# K-means with SSE method
def k_means_SSE(stack, mask, K, rand_seed, maxit, trials, CTF, F=0, T0=0, SA2=False, DEBUG=False):
	from utilities    import model_blank, get_im
	from utilities    import print_begin_msg, print_end_msg, print_msg
	from random       import seed, randint, shuffle
	from copy         import deepcopy
	from fundamentals import rot_shift2D, rot_shift3D
	from sys          import exit
	import time
	if CTF:
		from morphology		import ctf_2, ctf_1d
		from filter		    import filt_ctf, filt_table
		from fundamentals	import fftip
		from utilities		import get_arb_params
	
	# Simulate annealing use or not
	if T0 != 0: SA = True
	else:       SA = False

	if SA:
		# for simulate annealing
		from math   import exp
		from random import random

	# to bdb
	if stack.split(':')[0] == 'bdb':
		BDB   = True
		stack = stack.split(':')[1]
		DB    = EMAN2DB.open_db()
	else:
		BDB   = False

	# define parameters
	if BDB: N = EMUtil.get_image_count('bdb:' + stack)
	else:   N = EMUtil.get_image_count(stack)

	t_start = time.time()	
	
	# Information about images
	if BDB: image = get_im('bdb:' + stack, 0)
	else:   image = get_im(stack, 0)
	nx    = image.get_xsize()
	ny    = image.get_ysize()
	nz    = image.get_zsize()
	or_nx = nx
	or_ny = ny
	or_nz = nz
	
	buf   = model_blank(nx, ny, nz)
	if CTF: fftip(buf)
	
	if(rand_seed > 0):  seed(rand_seed)
	else:               seed()
	Cls = {}
	Cls['n']   = [0]*K     # number of objects in a given cluster
	Cls['ave'] = [0]*K     # value of cluster average
	Cls['var'] = [0]*K     # value of cluster variance
	Cls['Ji']  = [0]*K     # value of Ji
	Cls['k']   =  K	       # value of number of clusters
	Cls['N']   =  N
	assign     = [0]*N
	im_M       = []
	
        if CTF:
		parnames   = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
		ctf	   = {}
		ctf2       = {}
		Cls_ctf2   = {}
		ctf_params = get_arb_params(image, parnames)
		ctm        = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
		len_ctm	   = len(ctm)
	
	# Load images and init clusters
	print_msg('> Load images\n')
		
	if mask:
		import types
		if (type(mask) is types.StringType):
			mask = get_im(mask)
	
	# apply CTF if flag
	if BDB: DB.open_dict(stack)
	if CTF:
		for im in xrange(N):
			# obtain image
			if BDB: image = DB[stack][im]
			else:	image = get_im(stack, im)

			# apply parameters
			alpha  = image.get_attr('alpha')
			sx     = image.get_attr('sx')
			sy     = image.get_attr('sy')
			mirror = image.get_attr('mirror')
			image  = rot_shift2D(image, alpha, sx, sy, mirror)
									
			# obtain ctf
			ctf_params = get_arb_params(image, parnames)
			
			# apply ctf if flag
			if ctf_params[6]:
				ERROR("K-means cannot be performed on CTF-applied images", "k_means",1)
				return -1
			
			# store the ctf, allow limit acces file
			ctf[im]  = ctf_1d(or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			ctf2[im] = ctf_2( or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
	
			# apply mask
			if mask:	Util.mul_img(image, mask)
			
			# fft
			fftip(image)
			
			# store image
			im_M.append(image)
			
			# update info of images
			if im == 0:
				nx   = im_M[im].get_xsize()
				ny   = im_M[im].get_ysize()
				nz   = im_M[im].get_zsize()
				
				# compute the norm
				norm = nx*ny*nz
	else:
		for im in xrange(N):
			# obtain image
			if BDB: image = DB[stack][im]
			else:	image = get_im(stack, im)

			# 3D object
			if or_nz > 1:
				# apply parameters
				phi    = image.get_attr('phi')
				theta  = image.get_attr('theta')
				psi    = image.get_attr('psi')
				s3x    = image.get_attr('s3x')
				s3y    = image.get_attr('s3y')
				s3z    = image.get_attr('s3z')
				mirror = image.get_attr('mirror')
				image  = rot_shift3D(image, phi, theta, psi, s3x, s3y, s3z)
				if mirror: image.process_inplace('mirror', {'axis':'x'})
			# 2D object
			elif or_ny > 1:
				# apply parameters
				alpha  = image.get_attr('alpha')
				sx     = image.get_attr('sx')
				sy     = image.get_attr('sy')
				mirror = image.get_attr('mirror')
				image  = rot_shift2D(image, alpha, sx, sy, mirror)
												
			# apply mask
			if mask: image = Util.compress_image_mask(image, mask)
		
			# update info of images
			if im == 0:
				nx   = image.get_xsize()
				ny   = image.get_ysize()
				nz   = image.get_zsize()
				
				# compute the norm
				norm = nx*ny*nz
				
				# new buf size
				buf  = model_blank(nx, ny, nz)
			
			# store image
			im_M.append(image)

	if BDB: DB.close_dict(stack)
		
	## TRIALS
	if trials > 1:
		MemCls, MemJe, MemAssign = {}, {}, {}
	else:
		trials = 1
	ntrials = 0
	while ntrials < trials:
		ntrials += 1

		# for simulate annealing
		if SA: T = T0
	
		# Init the cluster by an image empty
		buf.to_zero()
		for k in xrange(K):
			Cls['ave'][k] = buf.copy()
			Cls['var'][k] = buf.copy()
			Cls['n'][k]   = 0
			Cls['Ji'][k]  = 0

		## Random method
		retrial = 20
		while retrial > 0:
			retrial -= 1
			i = 0
			for im in xrange(N):
				assign[im] = randint(0, K-1)
				Cls['n'][assign[im]] += 1
			flag,k = 1,K
			while k>0 and flag:
				k -= 1 
				if Cls['n'][k] == 0:
					flag = 0
					if retrial == 0:
						ERROR("Empty class in the initialization","k_means_SSE",1)
					for k in xrange(K):
						Cls['n'][k] = 0
			if flag == 1:
				retrial = 0
		
		if CTF:
			## Calculate averages ave = S CTF.F / S CTF**2, first init ctf2
			for k in xrange(K):	Cls_ctf2[k] = [0] * len_ctm
			
			for im in xrange(N):
				# compute Sum ctf2
				for i in xrange(len_ctm):	Cls_ctf2[assign[im]][i] += ctf2[im][i]
				
				# compute average first step
				CTFxF = filt_table(im_M[im], ctf[im])
				Util.add_img(Cls['ave'][assign[im]], CTFxF)
			
			for k in xrange(K):
				valCTF = [0] * len_ctm
				for i in xrange(len_ctm):	valCTF[i] = 1.0 / float(Cls_ctf2[k][i])
				Cls['ave'][k] = filt_table(Cls['ave'][k], valCTF)
			
			## Compute Ji = S(im - CTFxAve)**2 and Je = S Ji
			for n in xrange(N):
				CTFxAve		      = filt_table(Cls['ave'][assign[n]], ctf[n])
				Cls['Ji'][assign[n]] += CTFxAve.cmp("SqEuclidean", im_M[n]) / norm
			Je = 0
			for k in xrange(K):	  Je += Cls['Ji'][k]
		else:
			## Calculate averages
			for im in xrange(N):	Util.add_img(Cls['ave'][assign[im]], im_M[im])
			for k in xrange(K):	Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))
				
			# Compute Ji = S(im - ave)**2 and Je = S Ji
			Je = 0
			for n in xrange(N):	Cls['Ji'][assign[n]] += im_M[n].cmp("SqEuclidean",Cls['ave'][assign[n]])/norm
			for k in xrange(K):	Je += Cls['Ji'][k]	
				
		## Clustering		
		ite       = 0
		watch_dog = 0
		old_Je    = 0
		change    = True
		order     = range(N)

		if DEBUG: print 'init Je', Je
		
		print_msg('\n__ Trials: %2d _________________________________%s\n'%(ntrials, time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime())))

		while change and watch_dog < maxit:
			ite       += 1
			watch_dog += 1
			change     = False
			shuffle(order)
			if SA: ct_pert = 0

			for imn in xrange(N):
				# to select random image
				im = order[imn]
				assign_to = -1
				
				# compute SqEuclidean (objects and centroids)
				if CTF:
					# compute the minimum distance with centroids
					# CTF: (F - CTFxAve)**2
					CTFxAve = []
					for k in xrange(K):
						tmp = filt_table(Cls['ave'][k], ctf[im])
						CTFxAve.append(tmp.copy())
					res = Util.min_dist(im_M[im], CTFxAve)
				else:
					# compute the minimum distance with centroids
					res = Util.min_dist(im_M[im], Cls['ave'])

					
				# Simulate Annealing
				if SA:
					if SA2:
						dJe = [0.0] * K
						ni  = float(Cls['n'][assign[im]])
						di  = res['dist'][assign[im]]
						for k in xrange(K):
							if k != assign[im]:
								nj  = float(Cls['n'][k])
								dj  = res['dist'][k]
								
								dJe[k] = -( (nj/(nj+1))*(dj/norm) - (ni/(ni-1))*(di/norm) )
															
							else:
								dJe[k] = 0

						# norm <0 [-1;0], >=0 [0;+1], if just 0 norm to 1
						nbneg  =  0
						nbpos  =  0
						minneg =  0
						maxpos =  0
						for k in xrange(K):
							if dJe[k] < 0.0:
								nbneg += 1
								if dJe[k] < minneg: minneg = dJe[k]
							else:
								nbpos += 1
								if dJe[k] > maxpos: maxpos = dJe[k]
						if nbneg != 0:                   dneg = -1.0 / minneg
						if nbpos != 0 and maxpos != 0:   dpos =  1.0 / maxpos
						for k in xrange(K):
							if dJe[k] < 0.0: dJe[k] = dJe[k] * dneg
							else:
								if maxpos != 0: dJe[k] = dJe[k] * dpos
								else:           dJe[k] = 1.0

						# q[k]
						q      = [0.0] * K
						arg    = [0.0] * K
						maxarg = 0
						for k in xrange(K):
							arg[k] = dJe[k] / T
							if arg[k] > maxarg: maxarg = arg[k]
						limarg = 17
						if maxarg > limarg:
							sumarg = float(sum(arg))
							for k in xrange(K): q[k] = exp(arg[k] * limarg / sumarg)
						else:
							for k in xrange(K): q[k] = exp(arg[k])
										
						# p[k]
						p = [[0.0, 0] for i in xrange(K)]
						sumq = float(sum(q))
						for k in xrange(K):
							p[k][0] = q[k] / sumq
							p[k][1] = k
											
						p.sort()
						c = [0.0] * K
						c[0] = p[0][0]
						for k in xrange(1, K): c[k] = c[k-1] + p[k][0]

						pb = random()
						select = -1
						for k in xrange(K):
							if c[k] > pb:
								select = p[k][1]
								break
					

						if select != res['pos']:
							ct_pert    += 1
							res['pos']  = select

						
					else:
						if exp( -(1) / float(T) ) > random():
							res['pos']  = randint(0, K - 1)
							ct_pert    += 1
							
			
				# moving object and update iteratively
				if res['pos'] != assign[im]:
					assign_from = assign[im]
					assign_to   = res['pos']
								
					if CTF:
						# Update average
						
						# compute valCTF = CTFi / (S ctf2 - ctf2i)
						valCTF = [0] * len_ctm
						for i in xrange(len_ctm):
							valCTF[i] = Cls_ctf2[assign_from][i] - ctf2[im][i]
							valCTF[i] = ctf[im][i] / valCTF[i]
						# compute CTFxAve
						CTFxAve = filt_table(Cls['ave'][assign_from], ctf[im])
						# compute F - CTFxAve
						buf.to_zero()
						buf = Util.subn_img(im_M[im], CTFxAve) 
						# compute valCTF * (F - CTFxAve)
						buf = filt_table(buf, valCTF)
						# sub the value at the average
						Util.sub_img(Cls['ave'][assign_from], buf)

						# compute valCTF = CTFi / (S ctf2 + ctf2i)
						valCTF = [0] * len_ctm
						for i in xrange(len_ctm):
							valCTF[i] = ctf[im][i] / (Cls_ctf2[assign_to][i] + ctf2[im][i])
						# compute CTFxAve
						CTFxAve = filt_table(Cls['ave'][assign_to], ctf[im])
						# compute F - CTFxAve
						buf.to_zero()
						buf = Util.subn_img(im_M[im], CTFxAve) 
						# compute valCTF * (F - CTFxAve)
						buf = filt_table(buf, valCTF)
						# add the value at the average
						Util.add_img(Cls['ave'][assign_to], buf)	
					else:
						# Update average
						buf.to_zero()
						buf = Util.mult_scalar(Cls['ave'][assign_from], float(Cls['n'][assign_from]))
						Util.sub_img(buf,im_M[im])
						Cls['ave'][assign_from] = Util.mult_scalar(buf, 1.0/float(Cls['n'][assign_from]-1))

						buf.to_zero()
						buf = Util.mult_scalar(Cls['ave'][assign_to], float(Cls['n'][assign_to]))
						Util.add_img(buf, im_M[im])
						Cls['ave'][assign_to] = Util.mult_scalar(buf, 1.0/float(Cls['n'][assign_to]+1))
				
					
					# new number of objects in clusters
					Cls['n'][assign_from] -= 1
					assign[im]             = assign_to
					Cls['n'][assign_to]   += 1
					if CTF:
						# update Sum ctf2
						for i in xrange(len_ctm):
							Cls_ctf2[assign_from][i] -= ctf2[im][i]
							Cls_ctf2[assign_to][i]   += ctf2[im][i]
										
					# empty cluster control
					if Cls['n'][assign_from] == 1:
						print_msg('\nEmpty clusters!!\n')
						for k in xrange(K):	print_msg('Cls[%i]: %i\n'%(k, Cls['n'][k]))
						ERROR("Empty groups in kmeans_SSE","k_means_SSE",1)						
						exit()							
								
					change = True
			
			if CTF:
				## Compute Ji = S(im - CTFxAve)**2 and Je = S Ji
				for k in xrange(K): Cls['Ji'][k] = 0
				for n in xrange(N):
					CTFxAve		      = filt_table(Cls['ave'][assign[n]], ctf[n])
					Cls['Ji'][assign[n]] += CTFxAve.cmp("SqEuclidean", im_M[n]) / norm
				Je = 0
				for k in xrange(K):	  Je += Cls['Ji'][k]
			else:
				# Compute Je
				Je = 0
				for k in xrange(K):     Cls['Ji'][k] = 0
				for n in xrange(N):	Cls['Ji'][assign[n]] += im_M[n].cmp("SqEuclidean",Cls['ave'][assign[n]]) / norm
				for k in xrange(K):	Je += Cls['Ji'][k]
	
			# threshold convergence control
			if Je != 0:
				thd = abs(Je - old_Je) / Je
			else:
				thd = 0

			if SA:
				if thd < 1e-12 and ct_pert == 0: watch_dog = maxit
			else:
				if thd < 1e-8:	                 watch_dog = maxit
			old_Je = Je

			if SA:
				# Simulate annealing, update temperature
				T *= F
				if SA2:
					if T < 0.09: SA = False

				print_msg('> iteration: %5d    criterion: %11.6e    T: %13.8f  ct disturb: %5d\n' % (ite, Je, T, ct_pert))
				if DEBUG: print '> iteration: %5d    criterion: %11.6e    T: %13.8f  ct disturb: %5d' % (ite, Je, T, ct_pert)
			else:
				print_msg('> iteration: %5d    criterion: %11.6e\n'%(ite, Je))
				if DEBUG: print '> iteration: %5d    criterion: %11.6e'%(ite, Je)

		if CTF:
			## Calculate averages ave = S CTF.F / S CTF**2, first init ctf2
			for k in xrange(K):	Cls_ctf2[k] = [0] * len_ctm
			for im in xrange(N):
				# compute Sum ctf2
				for i in xrange(len_ctm):	Cls_ctf2[assign[im]][i] += ctf2[im][i]
				# compute average first step
				CTFxF = filt_table(im_M[im], ctf[im])
				Util.add_img(Cls['ave'][assign[im]], CTFxF)
			for k in xrange(K):
				valCTF = [0] * len_ctm
				for i in xrange(len_ctm):	valCTF[i] = 1.0 / float(Cls_ctf2[k][i])
				Cls['ave'][k] = filt_table(Cls['ave'][k], valCTF)
			## Compute Ji = S(im - CTFxAve)**2 and Je = S Ji
			for k in xrange(K): Cls['Ji'][k] = 0
			for n in xrange(N):
				CTFxAve		      = filt_table(Cls['ave'][assign[n]], ctf[n])
				Cls['Ji'][assign[n]] += CTFxAve.cmp("SqEuclidean", im_M[n]) / norm
			Je = 0
			for k in xrange(K):	  Je += Cls['Ji'][k]
		else:
			# Calculate the real averages, because the iterations method cause approximation
			buf.to_zero()
			for k in xrange(K):     Cls['ave'][k] = buf.copy()
			for im in xrange(N):	Util.add_img(Cls['ave'][assign[im]], im_M[im])
			for k in xrange(K):	Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))

			# Compute the accurate Je, because during the iterations Je is aproximated from average
			Je = 0
			for k in xrange(K):     Cls['Ji'][k] = 0
			for n in xrange(N):	Cls['Ji'][assign[n]] += im_M[n].cmp("SqEuclidean",Cls['ave'][assign[n]]) / norm
			for k in xrange(K):	Je += Cls['Ji'][k]	

		# memorize the result for this trial	
		if trials > 1:
			MemCls[ntrials-1]    = deepcopy(Cls)
			MemJe[ntrials-1]     = deepcopy(Je)
			MemAssign[ntrials-1] = deepcopy(assign)

			
	# if severals trials choose the best
	if trials > 1:
		val_min = 1.0e20
		best    = -1
		for n in xrange(trials):
			if MemJe[n] < val_min:
				val_min = MemJe[n]
				best    = n
		# affect the best
		Cls    = MemCls[best]
		Je     = MemJe[best]
		assign = MemAssign[best]
		
	if CTF:
		# compute the variance S (F - CTF * Ave)**2
		buf.to_zero()
		for k in xrange(K): Cls['var'][k] = buf.copy()
		
		for n in xrange(N):
			CTFxAve = filt_table(Cls['ave'][assign[n]], ctf[n])
			
			buf.to_zero()
			buf     = Util.subn_img(im_M[n], CTFxAve)
			Util.add_img(Cls['var'][assign[n]], buf) ## **2
		
	else:
		# compute the variance 1/n S(im-ave)**2 -> 1/n (Sim**2 - n ave**2)
		for im in xrange(N):	Util.add_img2(Cls['var'][assign[im]], im_M[im])
		for k in xrange(K):
			buf.to_zero()
			Util.add_img2(buf, Cls['ave'][k])
			Cls['var'][k] = Util.madn_scalar(Cls['var'][k], buf, -float(Cls['n'][k]))
			Util.mul_scalar(Cls['var'][k], 1.0/float(Cls['n'][k]))
			
			# Uncompress ave and var images if the mask is used
			if mask:
				Cls['ave'][k] = Util.reconstitute_image_mask(Cls['ave'][k], mask)
				Cls['var'][k] = Util.reconstitute_image_mask(Cls['var'][k], mask)

	# write the results if out_dire is defined
	if CTF:
		# ifft
		for k in xrange(K):
			fftip(Cls['ave'][k])
			fftip(Cls['var'][k])
			Cls['ave'][k].postift_depad_corner_inplace()
			Cls['var'][k].postift_depad_corner_inplace()

	# information display
	print_msg('\n')
	time_run = int(time.time() - t_start)
	time_h   = time_run / 3600
	time_m   = (time_run % 3600) / 60
	time_s   = (time_run % 3600) % 60
	print_msg('Time: %s h %s min %s s\n' % (str(time_h).rjust(2, '0'), str(time_m).rjust(2, '0'), str(time_s).rjust(2, '0')))
	print_msg('Criterion = %11.6e \n' % Je)
	for k in xrange(K):	print_msg('Cls[%i]: %i\n'%(k, Cls['n'][k]))
	#print_end_msg('k-means')

	## TEST
	if DEBUG: print Cls['n']
		
	# return Cls, assign and Je
	return Cls, assign
	
# K-means MPI with classical method
def k_means_cla_MPI(stack, out_dir, mask, K, rand_seed, maxit, trials, crit_name, CTF, GRP=0, myid=-1, main_node=-1, N_start=-1, N_stop=-1, IM=[-1], F=0, T0=0, SA2=False):
	from utilities    import model_blank, get_im, bcast_number_to_all
	from utilities    import bcast_EMData_to_all, reduce_EMData_to_root
	from utilities    import print_msg, print_begin_msg, print_end_msg
	from fundamentals import rot_shift2D, rot_shift3D
	from random       import seed, randint
	from copy	  import deepcopy
	from mpi 	  import mpi_init, mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	from mpi 	  import mpi_reduce, mpi_bcast, mpi_barrier, mpi_recv, mpi_send
	from mpi 	  import MPI_SUM, MPI_FLOAT, MPI_INT, MPI_LOR
	import time
	import sys
	if CTF:
		from morphology		import ctf_2, ctf_1d
		from filter		import filt_ctf, filt_table
		from fundamentals	import fftip
		from utilities		import get_arb_params

	# Simulate annealing
	if F != 0: SA = True
	else:      SA = False

	if SA:
		from math   import exp
		from random import random

	# to bdb
	if stack.split(':')[0] == 'bdb':
		BDB   = True
		stack = stack.split(':')[1]
		DB    = EMAN2DB.open_db()
	else:
		BDB   = False

	# [id]   part of code different for each node
	# [sync] synchronise each node
	# [main] part of code just for the main node
	# [all]  code write for all node
	
	if GRP == 0:
		# ------------------- MPI init ----------------------------- #
		# init
		sys.argv       = mpi_init(len(sys.argv),sys.argv)
		number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
		myid           = mpi_comm_rank(MPI_COMM_WORLD)

		# chose a random node as a main one
		main_node = 0
		if myid  == 0:	main_node = randint(0,number_of_proc-1)
		main_node = bcast_number_to_all(main_node,0)
		mpi_barrier(MPI_COMM_WORLD)

		# define the node affected to the images
		if BDB: N = EMUtil.get_image_count('bdb:' + stack)
		else:   N = EMUtil.get_image_count(stack)
		im_per_node = max(N/number_of_proc,1)
		N_start     = myid * im_per_node
		if myid == (number_of_proc-1):
			N_stop = N
		else:
			N_stop = min(N_start + im_per_node, N)
	else:
		N = len(IM)
		
	MPIlogfile_init(myid)
	MPIlogfile_print(myid, '************* Kind: Classical MPI *************\n')
	if BDB: MPIlogfile_print(myid, 'Stack name                  : %s (bdb file)\n' % stack)
	else:   MPIlogfile_print(myid, 'Stack name                  : %s\n' % stack)
	MPIlogfile_print(myid, 'Number of images            : %i\n' % N)
	MPIlogfile_print(myid, 'Output directory            : %s\n' % out_dir)
	MPIlogfile_print(myid, 'Number of clusters          : %i\n' % K)
	MPIlogfile_print(myid, 'Maskfile                    : %s\n' % mask)
	MPIlogfile_print(myid, 'Number of trials            : %i\n' % trials)
	MPIlogfile_print(myid, 'Optimization method         : Classical\n')
	if SA:
		MPIlogfile_print(myid, 'Simulate annealing          : ON\n')
		if SA2: MPIlogfile_print(myid, '  select neighbour          : closer according T\n')
		else:	MPIlogfile_print(myid, '  select neighbour          : randomly\n')
		MPIlogfile_print(myid, '  T0                        : %f\n' % T0)
		MPIlogfile_print(myid, '  F                         : %f\n' % F)
	else:
		MPIlogfile_print(myid, 'Simulate annealing          : OFF\n')
	MPIlogfile_print(myid, 'Maximum iteration           : %i\n'% maxit)
	MPIlogfile_print(myid, 'Data with CTF               : %s\n' % CTF)
	MPIlogfile_print(myid, 'Criterion                   : %s\n' % crit_name)
	MPIlogfile_print(myid, 'Random seed                 : %i\n' % rand_seed)
	MPIlogfile_print(myid, 'ID cpu                      : %i\n' % myid)
	if GRP == 0: MPIlogfile_print(myid, 'Number of cpus              : %i\n' % number_of_proc)
	MPIlogfile_print(myid, 'Images in this cpu          : %i to %i\n\n' % (N_start, N_stop - 1))

	t_start = time.time()
	
	# ---------------------------------------------------------- #

	# [all] Informations on images or mask for the norm
	if BDB: image = get_im('bdb:' + stack, N_start)
	else:   image = get_im(stack, N_start)
	nx    = image.get_xsize()
	ny    = image.get_ysize()
	nz    = image.get_zsize()
	or_nx = nx
	or_nz = nz
	or_ny = ny
	buf   = model_blank(nx,ny,nz)
	if CTF: fftip(buf)
	
	# [all] define parameters
	seed(rand_seed)
	Cls={}
	Cls['n']   = [0]*K   # number of objects in a given cluster
	Cls['ave'] = [0]*K   # value of cluster average
	Cls['var'] = [0]*K   # value of cluster variance
	Cls['Ji']  = [0]*K   # value of ji
	Cls['k']   =  K	     # value of number of clusters
	Cls['N']   =  N
	assign     = [0]*N
	im_M       = [0]*N
	
	if CTF:
		parnames    = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
		ctf	    = {}
		ctf2        = {}
		Cls_ctf2    = {}
		ctf_params  = get_arb_params(image, parnames)
		ctm         = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
		len_ctm	    = len(ctm)
		
	if mask:
		import types
		if (type(mask) is types.StringType):
			mask = get_im(mask)
	
	# apply CTF if flag
	if BDB and IM[0] == -1: DB.open_dict(stack)
	if CTF:
		for im in xrange(N_start, N_stop):
			# obtain image
			if IM[0] == -1:
				if BDB: image = DB[stack][im]
				else:	image = get_im(stack, im)
			else:
				image = IM[im].copy()

			# apply parameters
			alpha  = image.get_attr('alpha')
			sx     = image.get_attr('sx')
			sy     = image.get_attr('sy')
			mirror = image.get_attr('mirror')
			image  = rot_shift2D(image, alpha, sx, sy, mirror)
						
			# obtain ctf
			ctf_params = get_arb_params(image, parnames)
			
			# store the ctf, allow limit acces file
			ctf[im]  = ctf_1d(or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			ctf2[im] = ctf_2( or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			
			# apply mask
			if mask:	Util.mul_img(image, mask)
			
			# fft
			fftip(image)
			
			# store image
			im_M[im] = image.copy()
			
			# update info of images
			if im == N_start:
				nx   = im_M[im].get_xsize()
				ny   = im_M[im].get_ysize()
				nz   = im_M[im].get_zsize()
				
				# compute the norm
				norm = nx * ny * nz
	else:
		for im in xrange(N_start, N_stop):
			# obtain image
			if IM[0] == -1:
				if BDB: image = DB[stack][im]
				else:	image = get_im(stack, im)	
			else:
				image = IM[im].copy()

			# 3D object
			if or_nz > 1:
				# apply parameters
				phi    = image.get_attr('phi')
				theta  = image.get_attr('theta')
				psi    = image.get_attr('psi')
				s3x    = image.get_attr('s3x')
				s3y    = image.get_attr('s3y')
				s3z    = image.get_attr('s3z')
				mirror = image.get_attr('mirror')
				image  = rot_shift3D(image, phi, theta, psi, s3x, s3y, s3z)
				if mirror: image.process_inplace('mirror', {'axis':'x'})
			# 2D object
			elif or_ny > 1:
				# apply parameters
				alpha  = image.get_attr('alpha')
				sx     = image.get_attr('sx')
				sy     = image.get_attr('sy')
				mirror = image.get_attr('mirror')
				image  = rot_shift2D(image, alpha, sx, sy, mirror)
						
			# apply mask
			if mask:	image = Util.compress_image_mask(image, mask)
			
			# update info of images
			if im == N_start:
				nx   = image.get_xsize()
				ny   = image.get_ysize()
				nz   = image.get_zsize()
				
				# compute the norm
				norm = nx * ny * nz
				
				# new buf size
				buf  = model_blank(nx, ny, nz)
			
			# store image
			im_M[im] = image.copy()

	if BDB and IM[0] == -1: DB.close_dict(stack)
	del IM
	
	# TRIALS
	if trials > 1:
		MemCls, MemJe, MemAssign = {}, {}, {}
	else:
		trials = 1
	ntrials   = 0
	while ntrials < trials:
		ntrials  += 1

		# Simulate annealing
		if SA: T = T0
		
		# [all] Init the cluster by an image empty
		buf.to_zero()
		for k in xrange(K):
			Cls['ave'][k] = buf.copy()
			Cls['var'][k] = buf.copy()
			Cls['Ji'][k]  = 0
			Cls['n'][k]   = 0
			OldClsn       = [0] * K

		## [main] Random method
		if myid == main_node:
			retrial = 20
			while retrial > 0:
				retrial -= 1
				i = 0
				for im in xrange(N):
					assign[im] = randint(0, K-1)
					Cls['n'][int(assign[im])] += 1
				flag,k = 1,0
				while k < K and flag:
					if Cls['n'][k] == 0:
						flag = 0
						if retrial == 0:
							ERROR("Empty class in the initialization", "k_means_cla_MPI", 1)
						for k in xrange(K):
							Cls['n'][k] = 0
					k += 1
				if flag == 1: retrial = 0

		# [sync] waiting the assign is finished
		mpi_barrier(MPI_COMM_WORLD)

		# [all] send assign to the others proc and the number of objects in each clusters
		assign = mpi_bcast(assign, N, MPI_INT, main_node, MPI_COMM_WORLD)
		assign = assign.tolist()     # convert array gave by MPI to list
		Cls['n'] = mpi_bcast(Cls['n'], K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
		Cls['n'] = Cls['n'].tolist() # convert array gave by MPI to list
		
		## 
		if CTF:
			# [all] first init ctf2
			for k in xrange(K):	Cls_ctf2[k] = [0] * len_ctm
			
			# [id] compute local S ctf2 and local S ave	
			for im in xrange(N_start, N_stop):
				# ctf2
				for i in xrange(len_ctm):
					Cls_ctf2[int(assign[im])][i] += ctf2[im][i]
				# ave
				CTFxF = filt_table(im_M[im], ctf[im])
				Util.add_img(Cls['ave'][int(assign[im])], CTFxF)
			
			# [sync] waiting the result
			mpi_barrier(MPI_COMM_WORLD)
			
			# [all] compute global sum, broadcast the results and obtain the average ave = S CTF.F / S CTF**2
			for k in xrange(K):
				Cls_ctf2[k] = mpi_reduce(Cls_ctf2[k], len_ctm, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
				Cls_ctf2[k] = mpi_bcast(Cls_ctf2[k],  len_ctm, MPI_FLOAT, main_node, MPI_COMM_WORLD)
				Cls_ctf2[k] = Cls_ctf2[k].tolist()    # convert array gave by MPI to list
				
				reduce_EMData_to_root(Cls['ave'][k], myid, main_node)
				bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
				
				for i in xrange(len_ctm):	Cls_ctf2[k][i] = 1.0 / Cls_ctf2[k][i]
				Cls['ave'][k] = filt_table(Cls['ave'][k], Cls_ctf2[k])
								
		else:
			# [id] Calculates averages, first calculate local sum
			for im in xrange(N_start, N_stop):	Util.add_img(Cls['ave'][int(assign[im])], im_M[im])

			# [sync] waiting the result
			mpi_barrier(MPI_COMM_WORLD)

			# [all] compute global sum, broadcast the results and obtain the average
			for k in xrange(K):
				reduce_EMData_to_root(Cls['ave'][k], myid, main_node) 
				bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
				Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))
		
		## Clustering		
		ite       = 0
		watch_dog = 0
		old_Je    = 0
		change    = 1
		MPIlogfile_print(myid, '\n__ Trials: %2d _________________________________%s\n'%(ntrials, time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime())))
		
		while change and watch_dog < maxit:
			ite       += 1
			watch_dog += 1
			change     = 0
			Je         = 0
			if SA:
			   ct_pert = 0
			
			# [all] init the number of objects
			for k in xrange(K):	Cls['n'][k]=0

			# [id] assign each images with err_min between all clusters averages
			for im in xrange(N_start, N_stop):

				# [all] compute min dist between object and centroids
				if CTF:
					CTFxAve = []
					for k in xrange(K):
						tmp = filt_table(Cls['ave'][k], ctf[im])
						CTFxAve.append(tmp.copy())
					res = Util.min_dist(im_M[im], CTFxAve)
				else:
					res = Util.min_dist(im_M[im], Cls['ave'])

				# [all] Simulate annealing
				if SA:
					if SA2:
						dJe = [0.0] * K
						ni  = float(Cls['n'][assign[im]])
						di  = res['dist'][assign[im]]
						for k in xrange(K):
							if k != assign[im]:
								nj  = float(Cls['n'][k])
								dj  = res['dist'][k]
								
								dJe[k] = -( (nj/(nj+1))*(dj/norm) - (ni/(ni-1))*(di/norm) )
															
							else:
								dJe[k] = 0

						# norm <0 [-1;0], >=0 [0;+1], if just 0 norm to 1
						nbneg  =  0
						nbpos  =  0
						minneg =  0
						maxpos =  0
						for k in xrange(K):
							if dJe[k] < 0.0:
								nbneg += 1
								if dJe[k] < minneg: minneg = dJe[k]
							else:
								nbpos += 1
								if dJe[k] > maxpos: maxpos = dJe[k]
						if nbneg != 0:                   dneg = -1.0 / minneg
						if nbpos != 0 and maxpos != 0:   dpos =  1.0 / maxpos
						for k in xrange(K):
							if dJe[k] < 0.0: dJe[k] = dJe[k] * dneg
							else:
								if maxpos != 0: dJe[k] = dJe[k] * dpos
								else:           dJe[k] = 1.0

						# q[k]
						q      = [0.0] * K
						arg    = [0.0] * K
						maxarg = 0
						for k in xrange(K):
							arg[k] = dJe[k] / T
							if arg[k] > maxarg: maxarg = arg[k]
						limarg = 17
						if maxarg > limarg:
							sumarg = float(sum(arg))
							for k in xrange(K): q[k] = exp(arg[k] * limarg / sumarg)
						else:
							for k in xrange(K): q[k] = exp(arg[k])
										
						# p[k]
						p = [[0.0, 0] for i in xrange(K)]
						sumq = float(sum(q))
						for k in xrange(K):
							p[k][0] = q[k] / sumq
							p[k][1] = k
											
						p.sort()
						c = [0.0] * K
						c[0] = p[0][0]
						for k in xrange(1, K): c[k] = c[k-1] + p[k][0]

						pb = random()
						select = -1
						for k in xrange(K):
							if c[k] > pb:
								select = p[k][1]
								break
					

						if select != res['pos']:
							ct_pert    += 1
							res['pos']  = select

						
					else:
						if exp( -(1) / float(T) ) > random():
							res['pos']  = randint(0, K - 1)
							ct_pert    += 1
				
				# [all] move object
				if res['pos'] != assign[im]:
					assign[im]  = res['pos']
					change      = 1
					Je         += res['dist'] / norm
					
				# [id] calculate the new local number of objects
				Cls['n'][int(assign[im])] += 1
				
			# [sync] waiting the result
			mpi_barrier(MPI_COMM_WORLD)

			# [all] sum the number of objects in each node and broadcast
			Cls['n'] = mpi_reduce(Cls['n'], K, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
			Cls['n'] = mpi_bcast(Cls['n'], K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
			Cls['n'] = Cls['n'].tolist() # convert array gave by MPI to list
			
			# [all] init average and ctf2
			for k in xrange(K):
				if Cls['n'][k] < 1:
					ERROR("Empty groups in kmeans_classical","k_means_cla MPI",1)
					exit()			
				
				Cls['ave'][k].to_zero()
				Cls['Ji'][k] = 0
				if CTF:	Cls_ctf2[k] = [0] * len_ctm			
			
			if CTF:
				# [id] compute local S ctf2 and local S ave	
				for im in xrange(N_start, N_stop):
					# ctf2
					for i in xrange(len_ctm):
						Cls_ctf2[int(assign[im])][i] += ctf2[im][i]
					# ave
					CTFxF = filt_table(im_M[im], ctf[im])
					Util.add_img(Cls['ave'][int(assign[im])], CTFxF)
				
				# [sync] waiting the result
				mpi_barrier(MPI_COMM_WORLD)
				
				# [all] compute global sum, broadcast the results and obtain the average ave = S CTF.F / S CTF**2
				for k in xrange(K):
					Cls_ctf2[k] = mpi_reduce(Cls_ctf2[k], len_ctm, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
					Cls_ctf2[k] = mpi_bcast(Cls_ctf2[k], len_ctm, MPI_FLOAT, main_node, MPI_COMM_WORLD)
					Cls_ctf2[k] = Cls_ctf2[k].tolist() # convert array gave by MPI to list

					reduce_EMData_to_root(Cls['ave'][k], myid, main_node)
					bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
					
					for i in xrange(len_ctm):	Cls_ctf2[k][i] = 1.0 / float(Cls_ctf2[k][i])
					Cls['ave'][k] = filt_table(Cls['ave'][k], Cls_ctf2[k])

				# [id] compute Ji
				for im in xrange(N_start, N_stop):
					CTFxAve = filt_table(Cls['ave'][int(assign[im])], ctf[im])
					Cls['Ji'][int(assign[im])] += CTFxAve.cmp("SqEuclidean", im_M[im]) / norm

				# [all] waiting the result
				mpi_barrier(MPI_COMM_WORLD)

				# [all] global sum Ji
				Cls['Ji'] = mpi_reduce(Cls['Ji'], K, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
				Cls['Ji'] = mpi_bcast(Cls['Ji'],  K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
				Cls['Ji'] = Cls['Ji'].tolist()
			
			else:			
				# [id] Update clusters averages
				for im in xrange(N_start, N_stop):	Util.add_img(Cls['ave'][int(assign[im])], im_M[im])

				# [sync] waiting the result
				mpi_barrier(MPI_COMM_WORLD)

				# [all] compute global sum, broadcast the results and obtain the average
				for k in xrange(K):
					reduce_EMData_to_root(Cls['ave'][k], myid, main_node) 
					bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
					Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))

				# [id] compute Ji
				for im in xrange(N_start, N_stop): Cls['Ji'][int(assign[im])] += im_M[im].cmp("SqEuclidean", Cls['ave'][int(assign[im])])/norm


			# [all] compute Je
			Je = 0
			for k in xrange(K): Je += Cls['Ji'][k]

			# [all] waiting the result
			mpi_barrier(MPI_COMM_WORLD)

			# [all] calculate Je global sum and broadcast
			Je = mpi_reduce(Je, 1, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
			Je = mpi_bcast(Je, 1, MPI_FLOAT, main_node, MPI_COMM_WORLD)
			Je = Je.tolist()
			Je = Je[0]
			
			if SA:
				# Simulate annealing, update temperature
				T *= F
				if SA2:
					if T < 0.09: SA = False

				#[id] informations display
				MPIlogfile_print(myid, '> iteration: %5d    criterion: %11.6e   T: %13.8f  disturb:  %5d\n' % (ite, Je, T, ct_pert))
			else:
				# [id] informations display
				MPIlogfile_print(myid, '> iteration: %5d    criterion: %11.6e\n' % (ite, Je))
						
			# threshold convergence control
			if Je != 0: thd = abs(Je - old_Je) / Je
			else:       thd = 0
			if SA:
				if thd < 1e-12 and ct_pert == 0: change = 0
			else:
				if thd < 1e-8:	change = 0
			old_Je = Je
			
			# [all] Need to broadcast this value because all node must run together
			change = mpi_reduce(change, 1, MPI_INT, MPI_LOR, main_node, MPI_COMM_WORLD)
			change = mpi_bcast(change, 1, MPI_INT, main_node, MPI_COMM_WORLD)
			change = change.tolist()
			change = change[0]
		
		# [all] waiting the result
		mpi_barrier(MPI_COMM_WORLD)

		# [id] memorize the result for this trial	
		if trials > 1:
			MemCls[ntrials-1]    = deepcopy(Cls)
			MemJe[ntrials-1]     = deepcopy(Je)
			MemAssign[ntrials-1] = deepcopy(assign)
			
	# if severals trials choose the best
	if trials > 1:
		val_min = 1.0e20
		best    = -1
		for n in xrange(trials):
			if MemJe[n] < val_min:
				val_min = MemJe[n]
				best    = n
		# affect the best
		Cls    = MemCls[best]
		Je     = MemJe[best]
		assign = MemAssign[best]
	
	if CTF:
		# [id] compute Ji and the variance S (F - CTFxAve)**2
		for im in xrange(N_start, N_stop):
			CTFxAve = filt_table(Cls['ave'][int(assign[im])], ctf[im])
			Cls['Ji'][int(assign[im])] += CTFxAve.cmp("SqEuclidean", im_M[im]) / norm
			
			buf.to_zero()
			buf = Util.subn_img(CTFxAve, im_M[im])
			Util.add_img(Cls['var'][int(assign[im])], buf) # **2
		
		# [all] waiting the result
		mpi_barrier(MPI_COMM_WORLD)
		
		# [all] global sum Ji and var
		Cls['Ji'] = mpi_reduce(Cls['Ji'], K, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
		Cls['Ji'] = mpi_bcast(Cls['Ji'],  K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
		Cls['Ji'] = Cls['Ji'].tolist()
		for k in xrange(K):
			reduce_EMData_to_root(Cls['var'][k], myid, main_node)
			
	else:
		# [id] compute Ji and the variance 1/n S(im-ave)**2 -> 1/n (Sim**2 - n ave**2)	
		for im in xrange(N_start, N_stop):
			Cls['Ji'][int(assign[im])] += im_M[im].cmp("SqEuclidean", Cls['ave'][int(assign[im])])/norm		
			Util.add_img2(Cls['var'][int(assign[im])], im_M[im])
		
		# [all] waiting the result
		mpi_barrier(MPI_COMM_WORLD)

		# [all] global sum ji and im**2
		Cls['Ji'] = mpi_reduce(Cls['Ji'], K, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
		Cls['Ji'] = mpi_bcast(Cls['Ji'],  K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
		Cls['Ji'] = Cls['Ji'].tolist()
		
		for k in xrange(K): reduce_EMData_to_root(Cls['var'][k], myid, main_node)	
		
		
		# [main] caclculate the variance for each cluster
		if myid == main_node and out_dir != 'None':
		
			for k in xrange(K):
				buf.to_zero()
				Util.add_img2(buf, Cls['ave'][k])
				Cls['var'][k] = Util.madn_scalar(Cls['var'][k], buf, -float(Cls['n'][k]))
				Util.mul_scalar(Cls['var'][k], 1.0/float(Cls['n'][k]))
				
				# Uncompress ave and var images if the mask is used
				if mask:
					Cls['ave'][k] = Util.reconstitute_image_mask(Cls['ave'][k], mask)
					Cls['var'][k] = Util.reconstitute_image_mask(Cls['var'][k], mask)

	# [id] prepare assign to update
	v = range(N_start, N_stop)
	for n in xrange(N_start):
		assign[n] = 0
	for n in xrange(N_stop, N):
		assign[n] = 0
	# [all] gather in main_node
	assign = mpi_reduce(assign, N, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
	assign = assign.tolist() # convert array gave by MPI to list

	# [main_node] write the result
	if myid == main_node:
		# criterion
		MPIlogfile_print(myid, '\nStart computing criterion: ')			
		crit = k_means_criterion(Cls, crit_name)
		MPIlogfile_print(myid, ' [ok]\n')			

		if out_dir != 'None':
			if CTF:
				# ifft
				for k in xrange(K):
					fftip(Cls['ave'][k])
					fftip(Cls['var'][k])
					Cls['ave'][k].postift_depad_corner_inplace()
					Cls['var'][k].postift_depad_corner_inplace()

			# write result
			k_means_out_res(Cls, crit, assign, out_dir)
			
	# information display
	MPIlogfile_print(myid, '\n')
	time_run = int(time.time() - t_start)
	time_h   = time_run / 3600
	time_m   = (time_run % 3600) / 60
	time_s   = (time_run % 3600) % 60
	MPIlogfile_print(myid, 'Time: %s h %s min %s s\n' % (str(time_h).rjust(2, '0'), str(time_m).rjust(2, '0'), str(time_s).rjust(2, '0')))
	MPIlogfile_print(myid, 'Criterion = %11.4e \n' % Je)
	for k in xrange(K):	MPIlogfile_print(myid, 'Cls[%i]: %i\n'%(k, Cls['n'][k]))
	MPIlogfile_end(myid)

	if myid == main_node: return crit
	
# K-means MPI with SSE method
def k_means_SSE_MPI(stack, out_dir, mask, K, rand_seed, maxit, trials, crit_name, CTF, GRP=0, myid=-1, main_node=-1, N_start=-1, N_stop=-1, IM=[-1], F=0, T0=0, SA2=False):
	from utilities    import model_blank, get_im, bcast_number_to_all
	from utilities    import bcast_EMData_to_all, reduce_EMData_to_root
	from utilities    import print_begin_msg, print_end_msg, print_msg
	from random       import seed, randint, shuffle
	from fundamentals import rot_shift2D, rot_shift3D
	from copy	  import deepcopy
	from mpi 	  import mpi_init, mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	from mpi 	  import mpi_reduce, mpi_bcast, mpi_barrier, mpi_recv, mpi_send
	from mpi 	  import MPI_SUM, MPI_FLOAT, MPI_INT, MPI_LOR
	import time
	import sys
	if CTF:
		from morphology		import ctf_2, ctf_1d
		from filter		import filt_ctf, filt_table
		from fundamentals	import fftip
		from utilities		import get_arb_params	

	# Simulate annealing
	if F != 0: SA = True
	else:      SA = False

	if SA:
		from math   import exp
		from random import random

	# to bdb
	if stack.split(':')[0] == 'bdb':
		BDB   = True
		stack = stack.split(':')[1]
		DB    = EMAN2DB.open_db()
	else:
		BDB   = False
	
	# [id]   part of code different for each node
	# [sync] synchronise each node
	# [main] part of code just for the main node
	# [all]  code write for all node
	
	if GRP == 0:
		# ------------------- MPI init ----------------------------- #
		# init
		sys.argv       = mpi_init(len(sys.argv),sys.argv)
		number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
		myid           = mpi_comm_rank(MPI_COMM_WORLD)

		# chose a random node as a main one
		main_node = 0
		if myid  == 0: main_node = randint(0,number_of_proc-1)
		main_node = bcast_number_to_all(main_node,0)
		mpi_barrier(MPI_COMM_WORLD)

		# define the node affected to the images
		if BDB: N = EMUtil.get_image_count('bdb:' + stack)
		else:   N = EMUtil.get_image_count(stack)
		im_per_node = max(N/number_of_proc, 1)
		N_start     = myid * im_per_node
		if myid == (number_of_proc-1):
			N_stop = N
		else:
			N_stop = min(N_start + im_per_node, N) 
	else:
		N = len(IM)
			
	MPIlogfile_init(myid)
	MPIlogfile_print(myid, '************* Kind: SSE MPI *************\n')
	if BDB: MPIlogfile_print(myid, 'Stack name                  : %s (bdb file)\n' % stack)
	else:   MPIlogfile_print(myid, 'Stack name                  : %s\n' % stack)
	MPIlogfile_print(myid, 'Number of images            : %i\n' % N)
	MPIlogfile_print(myid, 'Output directory            : %s\n' % out_dir)
	MPIlogfile_print(myid, 'Number of clusters          : %i\n' % K)
	MPIlogfile_print(myid, 'Maskfile                    : %s\n' % mask)
	MPIlogfile_print(myid, 'Number of trials            : %i\n' % trials)
	MPIlogfile_print(myid, 'Optimization method         : SSE\n')
	if SA:
		MPIlogfile_print(myid, 'Simulate annealing          : ON\n')
		if SA2: MPIlogfile_print(myid, '  select neighbour          : closer according T\n')
		else:   MPIlogfile_print(myid, '  select neighbour          : randomly\n')
		MPIlogfile_print(myid, '  T0                        : %f\n' % T0)
		MPIlogfile_print(myid, '  F                         : %f\n' % F)
	else:
		MPIlogfile_print(myid, 'Simulate annealing          : OFF\n')
	MPIlogfile_print(myid, 'Maximum iteration           : %i\n' % maxit)
	MPIlogfile_print(myid, 'Data with CTF               : %s\n' % CTF)
	MPIlogfile_print(myid, 'Criterion                   : %s\n' % crit_name)
	MPIlogfile_print(myid, 'Random seed                 : %i\n' % rand_seed)
	MPIlogfile_print(myid, 'ID cpu                      : %i\n' % myid)
	if GRP == 0: MPIlogfile_print(myid, 'Number of cpus              : %i\n' % number_of_proc)
	MPIlogfile_print(myid, 'Images in this cpu          : %i to %i\n\n' % (N_start, N_stop - 1))
	
	t_start = time.time()	
		
	# ---------------------------------------------------------- #
		
	# [all] Informations on images or mask for the norm
	if BDB: image = get_im('bdb:' + stack, N_start)
	else:   image = get_im(stack, N_start)
	nx    = image.get_xsize()
	ny    = image.get_ysize()
	nz    = image.get_zsize()
	or_nx = nx
	or_ny = ny
	or_nz = nz
	buf   = model_blank(nx,ny,nz)
	if CTF: fftip(buf)	
	
	# [all] define parameters	
	seed(rand_seed)
	Cls={}
	Cls['n']   = [0]*K   # number of objects in a given cluster
	Cls['ave'] = [0]*K   # value of cluster average
	Cls['var'] = [0]*K   # value of cluster variance
	Cls['Ji']  = [0]*K   # value of ji
	Cls['k']   =  K	     # value of number of clusters
	Cls['N']   =  N
	assign     = [0]*N
	im_M       = [0]*N
	
	if CTF:
		parnames    = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
		ctf	    = {}
		ctf2        = {}
		Cls_ctf2    = {}
		ctf_params  = get_arb_params(image, parnames)
		ctm         = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
		len_ctm	    = len(ctm)
	
	if mask:
		import types
		if (type(mask) is types.StringType):
			mask = get_im(mask)
	
	# apply CTF if flag
	if BDB and IM[0] == -1: DB.open_dict(stack)
	if CTF:
		for im in xrange(N_start, N_stop):
			# obtain image
			if IM[0] == -1:
				if BDB: image = DB[stack][im]
				else:	image = get_im(stack, im)
			else:
				image = IM[im].copy()

			# apply parameters
			alpha  = image.get_attr('alpha')
			sx     = image.get_attr('sx')
			sy     = image.get_attr('sy')
			mirror = image.get_attr('mirror')
			image  = rot_shift2D(image, alpha, sx, sy, mirror)
						
			# obtain ctf
			ctf_params = get_arb_params(image, parnames)
			
			# store the ctf, allow limit acces file
			ctf[im]  = ctf_1d(or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			ctf2[im] = ctf_2( or_nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			
			# apply mask
			if mask:	Util.mul_img(image, mask)
			
			# fft
			fftip(image)
			
			# store image
			im_M[im] = image.copy()
			
			# update info of images
			if im == N_start:
				nx   = im_M[im].get_xsize()
				ny   = im_M[im].get_ysize()
				nz   = im_M[im].get_zsize()
				
				# compute the norm
				norm = nx * ny * nz
	else:
		for im in xrange(N_start, N_stop):

			# obtain image
			if IM[0] == -1:
				if BDB: image = DB[stack][im]
				else:	image = get_im(stack, im)
			else:
				image = IM[im].copy()

			# 3D object
			if or_nz > 1:
				# apply parameters
				phi    = image.get_attr('phi')
				theta  = image.get_attr('theta')
				psi    = image.get_attr('psi')
				s3x    = image.get_attr('s3x')
				s3y    = image.get_attr('s3y')
				s3z    = image.get_attr('s3z')
				mirror = image.get_attr('mirror')
				image  = rot_shift3D(image, phi, theta, psi, s3x, s3y, s3z)
				if mirror: image.process_inplace('mirror', {'axis':'x'})
			# 2D object
			elif or_ny > 1:
				# apply parameters
				alpha  = image.get_attr('alpha')
				sx     = image.get_attr('sx')
				sy     = image.get_attr('sy')
				mirror = image.get_attr('mirror')
				image  = rot_shift2D(image, alpha, sx, sy, mirror)
						
			# apply mask
			if mask:	image = Util.compress_image_mask(image, mask)
			
			# update info of images
			if im == N_start:
				nx   = image.get_xsize()
				ny   = image.get_ysize()
				nz   = image.get_zsize()
				
				# compute the norm
				norm = nx * ny * nz
				
				# new buf size
				buf  = model_blank(nx, ny, nz)
			
			# store image
			im_M[im] = image.copy()
			
	if BDB and IM[0] == -1: DB.close_dict(stack)
	del IM
	
	# TRIALS
	if trials > 1:
		MemCls, MemJe, MemAssign = {}, {}, {}
	else:
		trials = 1
	ntrials   = 0
	while ntrials < trials:
		ntrials += 1

		# Simulate annealing
		if SA: T = T0
		
		# [all] Init the cluster by an image empty
		buf.to_zero()
		for k in xrange(K):
			Cls['ave'][k] = buf.copy()
			Cls['var'][k] = buf.copy()
			Cls['Ji'][k]  = 0
			Cls['n'][k]   = 0
			OldClsn       = [0] * K
		
		## [main] Random method
		if myid == main_node:
			retrial = 20
			while retrial > 0:
				retrial -= 1
				i = 0
				for im in xrange(N):
					assign[im] = randint(0, K-1)
					Cls['n'][int(assign[im])] += 1
				flag,k = 1,0
				while k < K and flag:
					if Cls['n'][k] == 0:
						flag = 0
						if retrial == 0:
							ERROR("Empty class in the initialization","k_means_SSE_MPI",1)
						for k in xrange(K):
							Cls['n'][k] = 0
					k += 1
				if flag == 1:	retrial = 0
		
		# [sync] waiting the assign is finished
		mpi_barrier(MPI_COMM_WORLD)
		
		# [all] send assign to the others proc and the number of objects in each cluster
		assign = mpi_bcast(assign, N, MPI_INT, main_node, MPI_COMM_WORLD)
		assign = assign.tolist()     # convert array gave by MPI to list
		Cls['n'] = mpi_bcast(Cls['n'], K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
		Cls['n'] = Cls['n'].tolist() # convert array gave by MPI to list
			
		## 
		if CTF:
			# [all] first init ctf2
			for k in xrange(K):	Cls_ctf2[k] = [0] * len_ctm
			
			# [id] compute local S ctf2 and local S ave	
			for im in xrange(N_start, N_stop):
				# ctf2
				for i in xrange(len_ctm):
					Cls_ctf2[int(assign[im])][i] += ctf2[im][i]
				# ave
				CTFxF = filt_table(im_M[im], ctf[im])
				Util.add_img(Cls['ave'][int(assign[im])], CTFxF)
			
			# [sync] waiting the result
			mpi_barrier(MPI_COMM_WORLD)
			
			# [all] compute global sum, broadcast the results and obtain the average ave = S CTF.F / S CTF**2
			for k in xrange(K):
				Cls_ctf2[k] = mpi_reduce(Cls_ctf2[k], len_ctm, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
				Cls_ctf2[k] = mpi_bcast(Cls_ctf2[k],  len_ctm, MPI_FLOAT, main_node, MPI_COMM_WORLD)
				Cls_ctf2[k] = Cls_ctf2[k].tolist()    # convert array gave by MPI to list
				
				reduce_EMData_to_root(Cls['ave'][k], myid, main_node)
				bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
				
				valCTF = [0] * len_ctm
				for i in xrange(len_ctm):	valCTF[i] = 1.0 / Cls_ctf2[k][i]
				Cls['ave'][k] = filt_table(Cls['ave'][k], valCTF)
			
			# [all] waiting the result
			mpi_barrier(MPI_COMM_WORLD)
										
		else:
			# [id] Calculates averages, first calculate local sum
			for im in xrange(N_start, N_stop):	Util.add_img(Cls['ave'][int(assign[im])], im_M[im])

			# [sync] waiting the result
			mpi_barrier(MPI_COMM_WORLD)

			# [all] compute global sum, broadcast the results and obtain the average
			for k in xrange(K):
				reduce_EMData_to_root(Cls['ave'][k], myid, main_node) 
				bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
				Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))

			# [sync] waiting the result
			mpi_barrier(MPI_COMM_WORLD)

	
		## Clustering
		ite       = 0
		watch_dog = 0
		old_Je    = 0
		sway_Je   = [0] * 2
		sway_ct   = 0
		change    = 1
		loc_order = range(N_start, N_stop)
		MPIlogfile_print(myid, '\n__ Trials: %2d _________________________________%s\n'%(ntrials, time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime())))

		while change and watch_dog < maxit:
			ite       += 1
			watch_dog += 1
			change     = 0
			err	   = {}
			order	   = [0]*N
			index	   = 0
			Je	   = 0
			if SA:
			   ct_pert = 0
			shuffle(loc_order)	
				
			# [id] random number to image
			for n in xrange(N_start, N_stop):
				order[n] = loc_order[index]
				index   += 1
			imn = N_start
			all_proc_end = 0

			ct_update = 0
			th_update = (N_stop - N_start) / 5
			while imn < N_stop:
				# to select random image
				im        = order[imn]
				imn      +=  1
				
				# [all] compute min dist between object and centroids
				if CTF:
					CTFxAve = []
					for k in xrange(K):
						tmp = filt_table(Cls['ave'][k], ctf[im])
						CTFxAve.append(tmp.copy())
					res = Util.min_dist(im_M[im], CTFxAve)
					
				else:
					res = Util.min_dist(im_M[im], Cls['ave'])

					
				# [all] Simulate annealing
				if SA:
					if SA2:
						dJe = [0.0] * K
						ni  = float(Cls['n'][assign[im]])
						di  = res['dist'][assign[im]]											
						for k in xrange(K):
							if k != assign[im]:
								nj  = float(Cls['n'][k])
								dj  = res['dist'][k]
								
								dJe[k] = -( (nj/(nj+1))*(dj/norm) - (ni/(ni-1))*(di/norm) )
															
							else:
								dJe[k] = 0

						# norm <0 [-1;0], >=0 [0;+1], if just 0 norm to 1
						nbneg  =  0
						nbpos  =  0
						minneg =  0
						maxpos =  0
						for k in xrange(K):
							if dJe[k] < 0.0:
								nbneg += 1
								if dJe[k] < minneg: minneg = dJe[k]
							else:
								nbpos += 1
								if dJe[k] > maxpos: maxpos = dJe[k]
						if nbneg != 0:                   dneg = -1.0 / minneg
						if nbpos != 0 and maxpos != 0:   dpos =  1.0 / maxpos
						for k in xrange(K):
							if dJe[k] < 0.0: dJe[k] = dJe[k] * dneg
							else:
								if maxpos != 0: dJe[k] = dJe[k] * dpos
								else:           dJe[k] = 1.0

						# q[k]
						q      = [0.0] * K
						arg    = [0.0] * K
						maxarg = 0
						for k in xrange(K):
							arg[k] = dJe[k] / T
							if arg[k] > maxarg: maxarg = arg[k]
						limarg = 17
						if maxarg > limarg:
							sumarg = float(sum(arg))
							for k in xrange(K): q[k] = exp(arg[k] * limarg / sumarg)
						else:
							for k in xrange(K): q[k] = exp(arg[k])

						# p[k]
						p = [[0.0, 0] for i in xrange(K)]
						sumq = float(sum(q))
						for k in xrange(K):
							p[k][0] = q[k] / sumq
							p[k][1] = k
											
						p.sort()
						c = [0.0] * K
						c[0] = p[0][0]
						for k in xrange(1, K): c[k] = c[k-1] + p[k][0]

						pb = random()
						select = -1
						for k in xrange(K):
							if c[k] > pb:
								select = p[k][1]
								break
					

						if select != res['pos']:
							ct_pert    += 1
							res['pos']  = select

						
					else:
						if exp( -(1) / float(T) ) > random():
							res['pos']  = randint(0, K - 1)
							ct_pert    += 1
					
				# [all] moving object
				if res['pos'] != assign[im]:
					assign[im] = res['pos']
					change     = 1

				# count update
				ct_update += 1

				# if reach th update all (SSE)
				if ct_update > th_update:
					ct_update = 0
					
					# [id] compute the number of objects
					for k in xrange(K): 		  Cls['n'][k] = 0
					for n in xrange(N_start, N_stop): Cls['n'][int(assign[n])] += 1			

					# [all] sum the number of objects in each node and broadcast
					Cls['n'] = mpi_reduce(Cls['n'], K, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
					Cls['n'] = mpi_bcast(Cls['n'], K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
					Cls['n'] = Cls['n'].tolist() # convert array gave by MPI to list

					# [all] init average, Ji and ctf2
					for k in xrange(K):
						if Cls['n'][k] < 2:
							ERROR("Empty groups in kmeans_classical","k_means_SSE_MPI",1)
							exit()	

						Cls['ave'][k].to_zero()
						if CTF:	Cls_ctf2[k] = [0] * len_ctm	

					if CTF:
						# [id] compute local S ctf2 and local S ave	
						for im in xrange(N_start, N_stop):
							# ctf2
							for i in xrange(len_ctm):
								Cls_ctf2[int(assign[im])][i] += ctf2[im][i]
							# ave
							CTFxF = filt_table(im_M[im], ctf[im])
							Util.add_img(Cls['ave'][int(assign[im])], CTFxF)

						# [sync] waiting the result
						mpi_barrier(MPI_COMM_WORLD)

						# [all] compute global sum, broadcast the results and obtain the average ave = S CTF.F / S CTF**2
						for k in xrange(K):
							Cls_ctf2[k] = mpi_reduce(Cls_ctf2[k], len_ctm, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
							Cls_ctf2[k] = mpi_bcast(Cls_ctf2[k], len_ctm, MPI_FLOAT, main_node, MPI_COMM_WORLD)
							Cls_ctf2[k] = Cls_ctf2[k].tolist() # convert array gave by MPI to list

							reduce_EMData_to_root(Cls['ave'][k], myid, main_node)
							bcast_EMData_to_all(Cls['ave'][k], myid, main_node)

							valCTF = [0] * len_ctm
							for i in xrange(len_ctm):	valCTF[i] = 1.0 / float(Cls_ctf2[k][i])
							Cls['ave'][k] = filt_table(Cls['ave'][k], valCTF)
						
					else:			
						# [id] Update clusters averages
						for im in xrange(N_start, N_stop): Util.add_img(Cls['ave'][int(assign[im])], im_M[im])

						# [sync] waiting the result
						mpi_barrier(MPI_COMM_WORLD)

						# [all] compute global sum, broadcast the results and obtain the average
						for k in xrange(K):
							reduce_EMData_to_root(Cls['ave'][k], myid, main_node) 
							bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
							Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))

					# [all] waiting the result
					mpi_barrier(MPI_COMM_WORLD)
						
														
			# [sync]
			mpi_barrier(MPI_COMM_WORLD)
			
			# [id] compute the number of objects
			for k in xrange(K): 		  Cls['n'][k] = 0
			for n in xrange(N_start, N_stop): Cls['n'][int(assign[n])] += 1			

			# [all] sum the number of objects in each node and broadcast
			Cls['n'] = mpi_reduce(Cls['n'], K, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
			Cls['n'] = mpi_bcast(Cls['n'], K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
			Cls['n'] = Cls['n'].tolist() # convert array gave by MPI to list
			
			# [all] init average, Ji and ctf2
			for k in xrange(K):
				if Cls['n'][k] < 2:
					ERROR("Empty groups in kmeans_classical","k_means_SSE_MPI",1)
					exit()	
				
				Cls['ave'][k].to_zero()
				Cls['Ji'][k] = 0
				if CTF:	Cls_ctf2[k] = [0] * len_ctm	
			
			if CTF:
				# [id] compute local S ctf2 and local S ave	
				for im in xrange(N_start, N_stop):
					# ctf2
					for i in xrange(len_ctm):
						Cls_ctf2[int(assign[im])][i] += ctf2[im][i]
					# ave
					CTFxF = filt_table(im_M[im], ctf[im])
					Util.add_img(Cls['ave'][int(assign[im])], CTFxF)
				
				# [sync] waiting the result
				mpi_barrier(MPI_COMM_WORLD)
				
				# [all] compute global sum, broadcast the results and obtain the average ave = S CTF.F / S CTF**2
				for k in xrange(K):
					Cls_ctf2[k] = mpi_reduce(Cls_ctf2[k], len_ctm, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
					Cls_ctf2[k] = mpi_bcast(Cls_ctf2[k], len_ctm, MPI_FLOAT, main_node, MPI_COMM_WORLD)
					Cls_ctf2[k] = Cls_ctf2[k].tolist() # convert array gave by MPI to list

					reduce_EMData_to_root(Cls['ave'][k], myid, main_node)
					bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
					
					valCTF = [0] * len_ctm
					for i in xrange(len_ctm):	valCTF[i] = 1.0 / float(Cls_ctf2[k][i])
					Cls['ave'][k] = filt_table(Cls['ave'][k], valCTF)

				# [id] compute Ji
				for im in xrange(N_start, N_stop):
					CTFxAve = filt_table(Cls['ave'][int(assign[im])], ctf[im])
					Cls['Ji'][int(assign[im])] += CTFxAve.cmp("SqEuclidean", im_M[im]) / norm

				# [all] waiting the result
				mpi_barrier(MPI_COMM_WORLD)

				# [all] global sum Ji
				Cls['Ji'] = mpi_reduce(Cls['Ji'], K, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
				Cls['Ji'] = mpi_bcast(Cls['Ji'],  K, MPI_FLOAT, main_node, MPI_COMM_WORLD)
				Cls['Ji'] = Cls['Ji'].tolist()

				
			else:			
				# [id] Update clusters averages
				for im in xrange(N_start, N_stop): Util.add_img(Cls['ave'][int(assign[im])], im_M[im])

				# [sync] waiting the result
				mpi_barrier(MPI_COMM_WORLD)

				# [all] compute global sum, broadcast the results and obtain the average
				for k in xrange(K):
					reduce_EMData_to_root(Cls['ave'][k], myid, main_node) 
					bcast_EMData_to_all(Cls['ave'][k], myid, main_node)
					Cls['ave'][k] = Util.mult_scalar(Cls['ave'][k], 1.0/float(Cls['n'][k]))

				# [id] compute Ji
				for im in xrange(N_start, N_stop): Cls['Ji'][int(assign[im])] += im_M[im].cmp("SqEuclidean", Cls['ave'][int(assign[im])])/norm

			# [all] compute Je
			Je = 0
			for k in xrange(K): Je += Cls['Ji'][k]

			# [all] waiting the result
			mpi_barrier(MPI_COMM_WORLD)

			# [all] calculate Je global sum and broadcast
			Je = mpi_reduce(Je, 1, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)
			Je = mpi_bcast(Je, 1, MPI_FLOAT, main_node, MPI_COMM_WORLD)
			Je = Je.tolist()
			Je = Je[0]
			
			if SA:
				# Simulate annealing, update temperature
				T *= F
				if SA2:
					if T < 0.09: SA = False
				
				#[id] informations display
				MPIlogfile_print(myid, '> iteration: %5d    criterion: %11.6e   T: %13.8f  disturb:  %5d\n' % (ite, Je, T, ct_pert))
			else:
				#[id] informations display
				MPIlogfile_print(myid, '> iteration: %5d    criterion: %11.6e\n' % (ite, Je))
			
			# Convergence control: threshold on the criterion value
			if Je != 0: thd = abs(Je - old_Je) / Je
			else:       thd = 0
			if SA:
				if thd < 1e-12 and ct_pert == 0: change = 0
			else:
				if thd < 1e-8: change = 0

			# Convergence control: if Je sway, means clusters unstable, due to the parallel version of k-means
			# store Je_n, Je_(n-1), Je_(n-2)
			sway_Je[1] = sway_Je[0]
			sway_Je[0] = old_Je
			old_Je = Je

			# count the consecutive number of Je periods egal at 2 (if Je_n == Je_(n-2))
			if Je == sway_Je[1]: sway_ct += 1
			else:                sway_ct == 0
			# if more of 4 periods consecutive, stop the program, detection of clusters unstable
			if sway_ct == 4 and not SA:
				change = 0
				MPIlogfile_print(myid, '> Stop iteration, unstable cluster detected: Criterion sway.\n')
			
			# [all] Need to broadcast this value because all node must run together
			change = mpi_reduce(change, 1, MPI_INT, MPI_LOR, main_node, MPI_COMM_WORLD)
			change = mpi_bcast(change, 1, MPI_INT, main_node, MPI_COMM_WORLD)
			change = change.tolist()
			change = change[0]
			
		# [all] waiting the result
		mpi_barrier(MPI_COMM_WORLD)
				
		# [id] memorize the result for this trial	
		if trials > 1:
			MemCls[ntrials-1]    = deepcopy(Cls)
			MemJe[ntrials-1]     = deepcopy(Je)
			MemAssign[ntrials-1] = deepcopy(assign)
			
	# if severals trials choose the best
	if trials > 1:
		val_min = 1.0e20
		best    = -1
		for n in xrange(trials):
			if MemJe[n] < val_min:
				val_min = MemJe[n]
				best    = n
		# affect the best
		Cls    = MemCls[best]
		Je     = MemJe[best]
		assign = MemAssign[best]
	
	
	if CTF:
		# [id] the variance S (F - CTFxAve)**2
		for im in xrange(N_start, N_stop):
			CTFxAve = filt_table(Cls['ave'][int(assign[im])], ctf[im])
			buf.to_zero()
			buf = Util.subn_img(CTFxAve, im_M[im])
			Util.add_img(Cls['var'][int(assign[im])], buf) # **2
		
		# [all] waiting the result
		mpi_barrier(MPI_COMM_WORLD)
		
		# [all] global sum var
		for k in xrange(K): reduce_EMData_to_root(Cls['var'][k], myid, main_node)
		
		# compute criterion
		crit = k_means_criterion(Cls, assign, crit_name)
		
	else:
		# [id] compute the variance 1/n S(im-ave)**2 -> 1/n (Sim**2 - n ave**2)	
		for im in xrange(N_start, N_stop): Util.add_img2(Cls['var'][int(assign[im])], im_M[im])
		
		# [all] waiting the result
		mpi_barrier(MPI_COMM_WORLD)

		# [all] global sum var
		for k in xrange(K): reduce_EMData_to_root(Cls['var'][k], myid, main_node)	
		
		# [main] caclculate the variance for each cluster
		if myid == main_node and out_dir != 'None':
		
			for k in xrange(K):
				buf.to_zero()
				Util.add_img2(buf, Cls['ave'][k])
				Cls['var'][k] = Util.madn_scalar(Cls['var'][k], buf, -float(Cls['n'][k]))
				Util.mul_scalar(Cls['var'][k], 1.0/float(Cls['n'][k]))
				
				# Uncompress ave and var images if the mask is used
				if mask:
					Cls['ave'][k] = Util.reconstitute_image_mask(Cls['ave'][k], mask)
					Cls['var'][k] = Util.reconstitute_image_mask(Cls['var'][k], mask)
	
	# [id] prepare assign to update
	for n in xrange(N_start):
		assign[n] = 0
	for n in xrange(N_stop, N):
		assign[n] = 0
		
	# [all] gather in main_node
	assign = mpi_reduce(assign, N, MPI_INT, MPI_SUM, main_node, MPI_COMM_WORLD)
	assign = assign.tolist() # convert array gave by MPI to list

	# compute Ji global
	for k in xrange(K): Cls['Ji'][k] = mpi_reduce(Cls['Ji'][k], 1, MPI_FLOAT, MPI_SUM, main_node, MPI_COMM_WORLD)

	# [main_node] write the result
	if myid == main_node:
		
		# compute criterions
		MPIlogfile_print(myid, '\nStart computing criterion: ')			
		crit = k_means_criterion(Cls, crit_name)
		MPIlogfile_print(myid, ' [ok]\n')			

		if out_dir != 'None':
			if CTF:
				# ifft
				for k in xrange(K):
					fftip(Cls['ave'][k])
					fftip(Cls['var'][k])
					Cls['ave'][k].postift_depad_corner_inplace()
					Cls['var'][k].postift_depad_corner_inplace()
			# write result
			k_means_out_res(Cls, crit, assign, out_dir)

	# information display
	MPIlogfile_print(myid, '\n')
	time_run = int(time.time() - t_start)
	time_h   = time_run / 3600
	time_m   = (time_run % 3600) / 60
	time_s   = (time_run % 3600) % 60
	MPIlogfile_print(myid, 'Time: %s h %s min %s s\n' % (str(time_h).rjust(2, '0'), str(time_m).rjust(2, '0'), str(time_s).rjust(2, '0')))
	MPIlogfile_print(myid, 'Criterion = %11.6e \n' % Je)
	for k in xrange(K):	MPIlogfile_print(myid, 'Cls[%i]: %i\n'%(k, Cls['n'][k]))
	MPIlogfile_end(myid)

	# [all] waiting all nodes
	mpi_barrier(MPI_COMM_WORLD)

	if myid == main_node: return crit

def k_means_groups_serial(stack, out_file, mask, opt_method, K1, K2, rand_seed, maxit, trials, crit_name, CTF):
	from utilities  import print_begin_msg, print_end_msg, print_msg, get_im
	import time
	import string
	
	t_start = time.time()
	print_begin_msg('k-means groups')
		
	# watch file
	out = open('WATCH_GRP_KMEANS', 'w')
	out.write('Watch grp k-means ' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) +'\n')
	out.close()
	
	# open images
	N = EMUtil.get_image_count(stack)
	im = []
	for n in xrange(N):	im.append(get_im(stack, n))	
			
	Crit = {}
	KK   = range(K1, K2 + 1)	# Range of works
	if crit_name == 'all': crit_name='CHD'
	
	# init the criterion
	for name in crit_name:
		if name == 'C':		
			Crit['C']=[0] * len(KK)
			txt_C = ''
		elif name == 'H':
			Crit['H']=[0] * len(KK)
			txt_H = ''
		elif name == 'D':
			Crit['D']=[0] * len(KK)
			txt_DB = ''
		else:	ERROR("Kind of criterion k-means unknown","k_means_groups",1)
	
	# init the file result
	file_crit = open(out_file, 'w')
	file_crit.write('# Criterion of k-means group\n')
	txt = '# N  '
	for name in crit_name:
		if name == 'C':
			txt += '  Coleman'.ljust(13, ' ')
		elif name == 'H':
			txt += '  Harabasz'.ljust(13, ' ')
		elif name == 'D':
			txt += '  Davies-Bouldin'.ljust(13, ' ')
		else:
			ERROR("Kind of criterion k-means unknown","k_means_groups",1)
	txt += '\n'
	file_crit.write(txt)
		
	# Compute the criterion and format
	index = -1
	for K in KK:
		
		index += 1
		print_msg('\n')
		print_msg('|K=%3d|====================================================================\n' % K)
						
		if opt_method   == 'cla': [Cls, assign] = k_means_classical(stack, mask, K, rand_seed, maxit, trials, CTF)
		elif opt_method == 'SSE': [Cls, assign] = k_means_SSE(stack, mask, K, rand_seed, maxit, trials, CTF)
		else:			  ERROR("Kind of k-means unknown","k_means_groups",1)

		crit = k_means_criterion(Cls, crit_name)
		
		# watch file
		out = open('WATCH_GRP_KMEANS', 'a')
		out.write('%3d  C: %11.4e  H: %11.4e  DB: %11.4e | %s\n' % (K, crit['C'], crit['H'], crit['D'], time.ctime())) 
		out.close()
		
		# result file
		txt = '%3d ' % K
		ipos, pos = 2, {}
		for name in crit_name:
			if name == 'C':
				txt += '  %11.4e' % crit['C']
				pos['C'] = ipos
				Crit['C'][index]  = crit['C']
			elif name == 'H':
				txt += '  %11.4e' % crit['H']
				pos['H'] = ipos
				Crit['H'][index]  = crit['H']
			elif name == 'D':
				txt += '  %11.4e' % crit['D']
				pos['D'] = ipos
				Crit['D'][index]  = crit['D']
			ipos += 1
		txt += '\n'
		file_crit.write(txt)
		
	file_crit.close()	
	
	# make script file to gnuplot
	out = open(out_file + '.p', 'w')
	out.write('# Gnuplot script file for plotting result in kmeans groups\n')
	out.write('# cmd: gnuplot> load \x22%s.p\x22\n' % out_file)
	out.write('reset\n')
	out.write('set autoscale\n')
	txt = 'plot'
	
	for name in crit_name:
		if name == 'C':
			# norm plot [0;1]
			d = max(Crit['C']) - min(Crit['C'])
			a = 1 / d
			b = 0.5 - ((max(Crit['C']) * a + min(Crit['C']) * a) / 2)
			txt += ' \x22%s\x22 using 1:($%d*(%11.4e)+(%11.4e)) title \x22Coleman\x22 w l,' % (out_file, pos['C'], a, b)
		elif name == 'H':
			# norm plot [0;1]
			d = max(Crit['H']) - min(Crit['H'])
			a = 1 / d
			b = 0.5 - ((max(Crit['H']) * a + min(Crit['H']) * a) / 2)
			txt += ' \x22%s\x22 using 1:($%d*(%11.4e)+(%11.4e)) title \x22Harabasz\x22 w l,' % (out_file, pos['H'], a, b)
		elif name == 'D':
			# norm plot [0;1]
			d = max(Crit['D']) - min(Crit['D'])
			a = 1 / d
			b = 0.5 - ((max(Crit['D']) * a + min(Crit['D']) * a) / 2)
			txt += ' \x22%s\x22 using 1:($%d*(%11.4e)+(%11.4e)) title \x22Davies-Bouldin\x22 w l,' % (out_file, pos['D'], a, b)
	txt = txt.rstrip(',') + '\n'
	out.write(txt)
	out.close()
		
	# Watch file
	out = open('WATCH_GRP_KMEANS', 'a')
	out.write('Times: %f s\n' % (time.time()-t_start))
	out.close()
	print_end_msg('k-means groups')
		
	return Crit, KK

def k_means_groups_MPI(stack, out_file, mask, opt_method, K1, K2, rand_seed, maxit, trials, crit_name, CTF):
	from utilities  import bcast_number_to_all, get_im
	from utilities  import print_begin_msg, print_end_msg, print_msg
	from random     import seed, randint
	from mpi 	import mpi_init, mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	from mpi 	import mpi_reduce, mpi_bcast, mpi_barrier, mpi_recv, mpi_send
	from mpi 	import MPI_SUM, MPI_FLOAT, MPI_INT, MPI_LOR
	import sys
	import time
	
	# [id]   part of code different for each node
	# [sync] synchronise each node
	# [main] part of code just for the main node
	# [all]  code write for all node
	
	# ------------------- MPI init ----------------------------- #
	# init
	sys.argv       = mpi_init(len(sys.argv),sys.argv)
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid           = mpi_comm_rank(MPI_COMM_WORLD)
	
	# chose a random node as a main one
	main_node = 0
	if myid  == 0: main_node = randint(0,number_of_proc-1)
	main_node = bcast_number_to_all(main_node,0)
	mpi_barrier(MPI_COMM_WORLD)

	# define the node affected to the numbers tests
	KK = range(K1, K2+1)	# Range of works
	Nk = len(KK)
	
	# define the node affected to the images
	N 	    = EMUtil.get_image_count(stack)
	im_per_node = max(N/number_of_proc,1)
	N_start     = myid * im_per_node
	if myid == (number_of_proc-1):
		N_stop = N
	else:
		N_stop = min(N_start + im_per_node, N)
		
		
	if myid == main_node:
		t_start = time.time()
		# watch file
		out = open('WATCH_MPI_GRP_KMEANS', 'w')
		out.write('Watch grp k-means ' + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) +'\n')
		out.close()
	# --------------------------------------------------------- #
	
	Crit = {}
	if crit_name == 'all': crit_name='CHD'
	
	#[all] init the criterion
	# init the criterion
	for name in crit_name:
		if name == 'C':		
			Crit['C']=[0] * len(KK)
			txt_C = ''
		elif name == 'H':
			Crit['H']=[0] * len(KK)
			txt_H = ''
		elif name == 'D':
			Crit['D']=[0] * len(KK)
			txt_DB = ''
		else:	ERROR("Kind of criterion k-means unknown","k_means_groups",1)
	
	# init the file result
	if myid == main_node:
		file_crit = open(out_file, 'w')
		file_crit.write('# Criterion of k-means group\n')
		txt = '# N  '
		for name in crit_name:
			if name == 'C':
				txt += '  Coleman'.ljust(13, ' ')
			elif name == 'H':
				txt += '  Harabasz'.ljust(13, ' ')
			elif name == 'D':
				txt += '  Davies-Bouldin'.ljust(13, ' ')
			else:
				ERROR("Kind of criterion k-means unknown","k_means_groups",1)
		txt += '\n'
		file_crit.write(txt)
	
	# open image
	IM = [0]*N
	for im in xrange(N_start, N_stop):
		IM[im] = get_im(stack, im)
	
	index = -1			
	# [id] Measure the criterions
	for K in KK:

		index += 1
		
		if opt_method == 'cla':   crit = k_means_cla_MPI(stack, 'None', mask, K, rand_seed, maxit, trials, crit_name, CTF, 1, myid, main_node, N_start, N_stop, IM)
		elif opt_method == 'SSE': crit = k_means_SSE_MPI(stack, 'None', mask, K, rand_seed, maxit, trials, crit_name, CTF, 1, myid, main_node, N_start, N_stop, IM)
		else:                     ERROR('kind of k-means unknown', 'k_means_groups', 1)

		mpi_barrier(MPI_COMM_WORLD)

		# [main] Format and export the result
		if myid == main_node:
			# watch file
			out = open('WATCH_MPI_GRP_KMEANS', 'a')
			out.write('%d  C: %11.4e  H: %11.4e  DB: %11.4e | %s\n' % (K, crit['C'], crit['H'], crit['D'], time.ctime())) 
			out.close()

			# result file
			txt = '%3d ' % K
			ipos, pos = 2, {}
			for name in crit_name:
				if name == 'C':
					txt += '  %11.4e' % crit['C']
					pos['C'] = ipos
					Crit['C'][index]  = crit['C']	# Coleman
				elif name == 'H':
					txt += '  %11.4e' % crit['H']
					pos['H'] = ipos
					Crit['H'][index]  = crit['H']	# Harabasz
				elif name == 'D':
					txt += '  %11.4e' % crit['D']
					pos['D'] = ipos
					Crit['D'][index]  = crit['D']	# Davies & Bouldin
				ipos += 1
			txt += '\n'
			file_crit.write(txt)

	if myid == main_node:
		# make script file to gnuplot
		out = open(out_file + '.p', 'w')
		out.write('# Gnuplot script file for plotting result in kmeans groups\n')
		out.write('# cmd: gnuplot> load \x22%s.p\x22\n' % out_file)
		out.write('reset\n')
		out.write('set autoscale\n')
		txt = 'plot'

		for name in crit_name:
			if name == 'C':
				# norm plot [0;1]
				d = max(Crit['C']) - min(Crit['C'])
				a = 1 / d
				b = 0.5 - ((max(Crit['C']) * a + min(Crit['C']) * a) / 2)
				txt += ' \x22%s\x22 using 1:($%d*(%11.4e)+(%11.4e)) title \x22Coleman\x22 w l,' % (out_file, pos['C'], a, b)
			elif name == 'H':
				# norm plot [0;1]
				d = max(Crit['H']) - min(Crit['H'])
				a = 1 / d
				b = 0.5 - ((max(Crit['H']) * a + min(Crit['H']) * a) / 2)
				txt += ' \x22%s\x22 using 1:($%d*(%11.4e)+(%11.4e)) title \x22Harabasz\x22 w l,' % (out_file, pos['H'], a, b)
			elif name == 'D':
				# norm plot [0;1]
				d = max(Crit['D']) - min(Crit['D'])
				a = 1 / d
				b = 0.5 - ((max(Crit['D']) * a + min(Crit['D']) * a) / 2)
				txt += ' \x22%s\x22 using 1:($%d*(%11.4e)+(%11.4e)) title \x22Davies-Bouldin\x22 w l,' % (out_file, pos['D'], a, b)
		txt = txt.rstrip(',') + '\n'
		out.write(txt)
		out.close()
		
		# Watch file
		out = open('WATCH_MPI_GRP_KMEANS', 'a')
		out.write('Times: %f s\n'%(time.time()-t_start))
		out.close()

		file_crit.close()	

## END K-MEANS OLD HDF VERSION ################################################################
###############################################################################################


'''

def ali2d_cross_res(stack, outdir, maskfile=None, ir=1, ou=-1, rs=1, xr="4 2 1 1", yr="-1", ts="2 1 0.5 0.25", center=1, maxit=0, CTF=False, snr=1.0, user_func_name="ref_ali2d"):
 	"""
		Split data into odd and even data sets and align them seperately
		Cross resolution alignment
	"""
	import os
	from utilities 		import model_circle, model_blank, combine_params2, dropImage
	from utilities      import get_input_from_string, getImage, get_arb_params, set_arb_params
	from fundamentals 	import rot_shift2D
	from statistics 	import add_oe_series, ave_series_ctf, ave_series, fsc_mask
	from alignment 		import Numrinit, ringwe, ali2d_s, align2d
	from filter 		import filt_table, filt_ctf
	from morphology     import ctf_2

	from utilities import print_begin_msg, print_end_msg, print_msg
	import	types
		
	print_begin_msg("ali2d_cross_res")

	import user_functions
	user_func = user_functions.factory[user_func_name]

	xrng        = get_input_from_string(xr)
	if  yr == "-1":  yrng = xrng
	else          :  yrng = get_input_from_string(yr)
	step        = get_input_from_string(ts)

	first_ring=int(ir); last_ring=int(ou); rstep=int(rs); max_iter=int(maxit);

	if max_iter == 0:
		max_iter  = 10
		auto_stop = True
	else:
		auto_stop = False

	print_msg("Input stack                 : %s\n"%(stack))
	print_msg("Output directory            : %s\n"%(outdir))
	print_msg("Inner radius                : %i\n"%(first_ring))

	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack, 0)
	nx = ima.get_xsize()
	# default value for the last ring
	if (last_ring == -1):  last_ring = nx//2-2

	print_msg("Outer radius                : %i\n"%(last_ring))
	print_msg("Ring step                   : %i\n"%(rstep))
	print_msg("X search range              : %s\n"%(xrng))
	print_msg("Y search range              : %s\n"%(yrng))
	print_msg("Translational step          : %s\n"%(step))
	print_msg("Center type                 : %i\n"%(center))
	print_msg("Maximum iteration           : %i\n"%(max_iter))
	print_msg("Data with CTF               : %s\n"%(CTF))
	print_msg("Signal-to-Noise Ratio       : %f\n"%(snr))
	if auto_stop:  print_msg("Stop iteration with         : criterion\n")
	else:           print_msg("Stop iteration with         : maxit\n")

	if os.path.exists(outdir):
		os.system('rm -rf '+outdir)
	os.mkdir(outdir)

	if maskfile:
		if(type(maskfile) is types.StringType):
			print_msg("Maskfile                    : %s\n\n"%(maskfile))
			mask=getImage(maskfile)
		else:
			print_msg("Maskfile                    : user provided in-core mask\n\n")
			mask = maskfile
	else :
		print_msg("Maskfile                    : default, a circle with radius %i\n\n"%(last_ring))
		mask = model_circle(last_ring, nx, nx)

	#  ODD-EVEN is controlled by setting NG to 2
	NG = 2
	cnx = int(nx/2)+1
 	cny = cnx
 	mode = "F"
	data = [[] for i in xrange(NG)]
	all_data = []
	if(CTF):
		parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor",  "ctf_applied"]
		#                        0                1              2     3              4                5                6
		ctf_params = get_arb_params(ima, parnames)
		data_had_ctf = ctf_params[6]
		ctm = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
		lctf = len(ctm)
		ctf2 = [[[0.0]*lctf for j in xrange(2)] for i in xrange(NG)]
		ctfb2 = [[0.0]*lctf for i in xrange(NG)]
	for im in xrange(nima):
		k = im%NG
		ima = EMData()
		ima.read_image(stack, im)
		if(CTF):
			ctf_params = get_arb_params(ima, parnames)
			ctm = ctf_2(nx, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
			kl = (im//2)%NG  # not sure it will work for NG>2
			for i in xrange(lctf):
				ctf2[k][kl][i] += ctm[i]
			if(ctf_params[6] == 0):
				st = Util.infomask(ima, mask, False)
				ima -= st[0]
				#      filt_ctf(image,	     dz,		  cs,		   voltage,	     pixel_size,     amp_contrast=0.1,	  b_factor=0.0):
				ima = filt_ctf(ima, ctf_params[1], ctf_params[3], ctf_params[2], ctf_params[0], ctf_params[4], ctf_params[5])
				ima.set_attr('ctf_applied', 1)
		data[k].append(ima)

	if(CTF):
		ctf_tot = [0.0]*lctf
		for i in xrange(lctf):
			for k in xrange(NG):
				ctf_tot[i] += ctf2[k][0][i] + ctf2[k][1][i]
			ctf_tot[i] = 1.0/(ctf_tot[i] + 1.0/snr)
		for k in xrange(NG):
			for i in xrange(lctf):
				ctfb2[k][i] = 1.0/(ctf2[k][0][i] + ctf2[k][1][i] + 1.0/snr)
				for kl in xrange(2):
					ctf2[k][kl][i] = 1.0/(ctf2[k][kl][i] + 1.0/snr)
 	#precalculate rings
	numr = Numrinit(first_ring, last_ring, rstep, mode)
 	wr = ringwe(numr, mode)
	tavg = [None]*NG
	for k in xrange(NG):
		av1, av2 = add_oe_series(data[k])
		Util.add_img(av1, av2)
		if(CTF):  tavg[k] = filt_table(av1, ctfb2[k])
		else:	  tavg[k] = av1/len(data[k])
		dropImage(tavg[k],os.path.join(outdir, "aqc_%03d_%03d.hdf"%(k, 0)))
	fscross = fsc_mask(tavg[0], tavg[1], mask, 1.0, os.path.join(outdir, "drcross_%03d"%(0)))

	total_ave = model_blank(nx,nx)
	if(CTF):
		for k in xrange(NG):
			Util.add_img(total_ave, ave_series_ctf(data[k], ctf_tot))
	else:
		for k in xrange(NG):
			Util.add_img(total_ave, ave_series(data[k])*len(data[k]))
		total_ave /= nima
	dropImage(total_ave, os.path.join(outdir, "total_ave_%03d.hdf"%(0)))
	a0 = total_ave.cmp("dot", total_ave, dict(negative = 0, mask = mask))
	msg = "Initial criterion = %-20.7e\n"%(a0)
	print_msg(msg)
	params = ["alpha", "sx", "sy", "mirror"]
	# initialize data for the reference preparation function
	#  mask can be modified in user_function
	ref_data = []
	ref_data.append( mask )
	ref_data.append( center )
	cs=[[0.0,0.0]]*NG
	total_iter = 0
	for N_step in xrange(len(xrng)):
		msg = "\nX range = %5.2f   Y range = %5.2f   Step = %5.2f\n"%(xrng[N_step], yrng[N_step], step[N_step])
		print_msg(msg)
		for Iter in xrange(max_iter):
			total_iter += 1
			frsc = []
			ktavg = [None]*NG
			for k in xrange(NG):
				ali2d_s(data[k], numr, wr, cs[k], tavg[k], cnx, cny, xrng[N_step], yrng[N_step], step[N_step], mode, range(len(data[k])))
				av1, av2 = add_oe_series(data[k])
				if(CTF):
					tavg[k] = filt_table(Util.addn_img(av1, av2), ctfb2[k])
					av1    = filt_table(av1, ctf2[k][0])
					av2    = filt_table(av2, ctf2[k][1])
				else:
					tavg[k] = (av1+av2)/len(data[k])
				dropImage(tavg[k], os.path.join(outdir, "aqc_%03d_%03d.hdf"%(k, total_iter)))

				frsc.append(fsc_mask(av1, av2, ref_data[0], 1.0, os.path.join(outdir, "drc_%03d_%03d"%(k, total_iter))))
				#  prepare averages for alignment
				kref_data = []
				kref_data.append( mask )
				kref_data.append( 0 )
				kref_data.append( tavg[k] )
				kref_data.append( frsc[k] )
				#  call the user-supplied function to prepare reference image, i.e., filter it, but do not center!
				ktavg[k], cs[k] = user_func( kref_data )
				del kref_data
			#  This should be done only for estimation of resolution, nothing else!
			alpha, sx, sy, mirror, peak = align2d(ktavg[0], ktavg[1], xrng[0], yrng[0], step=0.25, first_ring = first_ring, last_ring = last_ring, rstep=1, mode = mode)
			#  apply parameters to the original average
			favg2 = rot_shift2D(tavg[0], alpha, sx, sy, mirrorm interpolation_method="gridding")
			fscross = fsc_mask(favg2, tavg[1], ref_data[0], 1.0, os.path.join(outdir, "drcross_%03d"%(total_iter)))
			del favg2
			# Here one may want to apply rot-shift of the first average to all images in its group
			for im in xrange(len(data[0])):
				ps = get_arb_params(data[0][im], params)
				an,sxn,syn,mrn = combine_params2(ps[0], ps[1], ps[2], ps[3], alpha, sx, sy, mirror)
				set_arb_params(data[0][im], [an,sxn,syn,mrn], params)
			k = 0
			av1, av2 = add_oe_series(data[k])
			if(CTF):
				tavg[k] = filt_table(Util.addn_img(av1, av2), ctfb2[k])
			else:
				tavg[k] = (av1+av2)/len(data[k])
			#  Here we have to change fsc values.  The reason is that we have crossresolution, so snr can be calculated directly,
			#        while in user function the fit to fsc is done under assumption that is was calculated by splitting the dataset, so it has a factor of 2
			for i in xrange(len(fscross[1])):   fscross[1][i] = fscross[1][i]/(2.0-fscross[1][i])
			for k in xrange(NG):
				#  Apply the same filtration to all averages
				ref_data.append( tavg[k] )
				ref_data.append( fscross  )
				#  call the user-supplied function to prepare reference image, i.e., filter and center!
				tavg[k], cs[k] = user_func( ref_data )
				del ref_data[2]
				del ref_data[2]
				dropImage(tavg[k], os.path.join(outdir, "aqf_%03d_%03d.hdf"%(k, total_iter)))
			total_ave = model_blank(nx,nx)
			if(CTF):
				for k in xrange(NG):
					Util.add_img(total_ave, ave_series_ctf(data[k], ctf_tot))
			else:
				for k in xrange(NG):
					Util.add_img(total_ave, ave_series(data[k])*len(data[k]))
				total_ave /= nima
			dropImage(total_ave, os.path.join(outdir, "total_ave_%03d.hdf"%(total_iter)))
			# a0 should increase; stop algorithm when it decreases.
			a1 = total_ave.cmp("dot", total_ave, dict(negative = 0, mask = ref_data[0]))
			msg = "ITERATION #%3d	     criterion = %20.7e\n"%(total_iter,a1)
			print_msg(msg)
			if(a1 < a0):
				if (auto_stop == True): break
			else:	a0 = a1
	# write out headers
	if(CTF and data_had_ctf == 0):
		for k in xrange(NG):
			for im in xrange(len(data[k])):
				data[k][im].set_attr('ctf_applied', 0)
	for im in xrange(nima):
		k=im%NG
		imm = im//NG
		data[k][imm].write_image(stack, im, EMUtil.ImageType.IMAGE_HDF, True)
	print_end_msg("ali2d_cross_res")
'''



# I'll put everything used in alignment based on SSNR here.
def err_func(args, data):
	from utilities import compose_transform2
	from math import sin, pi, sqrt
	
	v1 = data[0]
	v2 = data[1]
	nima = data[2]
	mirror_same = data[3]
	mirror_flip = data[4]

	err = 0.0
	alpha2 = args[0]
	sx2 = args[1]
	sy2 = args[2]
	for im in xrange(nima):
		mirror = v1[im*4+3]
		mirror_i = v2[im*4+3]
		if mirror == mirror_i:
			alpha = v1[im*4]
			sx = v1[im*4+1]
			sy = v1[im*4+2]
			alpha_i2 = v2[im*4]
			sx_i2 = v2[im*4+1]
			sy_i2 = v2[im*4+2]
			sign = 1-2*mirror
			if mirror_flip: sign = -sign
			alpha3, sx3, sy3, scale3 = compose_transform2(alpha*sign, sx*sign, sy, 1.0, alpha2, sx2, sy2, 1.0)
			this_err = 50*abs(sin((alpha3-alpha_i2)/180.0*pi/2))+sqrt((sx3-sx_i2)**2+(sy3-sy_i2)**2) 
			err += this_err
	return -err/mirror_same

def ave_ali_err(stack):
	from utilities import inverse_transform2, amoeba, get_params2D
	from math import sqrt

	nima = EMUtil.get_image_count(stack)
	v1 = []
	v2 = []
	mirror_same = 0 
	for im in xrange(nima):
		img = EMData()
		img.read_image(stack,im)
		alpha, sx, sy, mirror, dummy = get_params2D(img)
		v1.append(alpha)
		v1.append(sx)
		v1.append(sy)
		v1.append(mirror)
		alpha_i = img.get_attr("alpha_i")
		sx_i = img.get_attr("sx_i")
		sy_i = img.get_attr("sy_i")
		mirror_i = img.get_attr("mirror_i")
		if mirror==mirror_i:	mirror_same += 1
		alpha_i2, sx_i2, sy_i2, scale2 = inverse_transform2(alpha_i, sx_i, sy_i)
		v2.append(alpha_i2)
		v2.append(sx_i2)
		v2.append(sy_i2)
		v2.append(mirror_i)

	same_rate = float(mirror_same)/nima
	mirror_flip = False
	if same_rate < 0.5:
		mirror_flip = True
		for im in xrange(nima):
			v2[im*4+3]=1-v2[im*4+3]
		mirror_same = nima-mirror_same
		same_rate = 1-same_rate
	
	data = []
	data.append(v1)
	data.append(v2)
	data.append(nima)
	data.append(mirror_same)
	data.append(mirror_flip)

	ic = 0
	min_err = 1e10
	min_ali = []
	break_flag = False
	for i in xrange(36):
		alpha = 10*i
		for x in xrange(7):
			sx = x-3
			for y in xrange(7):
				sy = y-3
				args = [alpha, sx, sy]
				ic += 1  
				ps = amoeba(args, [1.0, 1.0, 1.0], err_func, 1.e-5, 1.e-5, 1000, data)
				err = -ps[1]
				if err < min_err:
					min_err = err
					min_ali = ps[0]
				# Our experenice shows that 20 trials is already more than enough to get 
				if ic==10: 
					break_flag = True
					break
			if break_flag: break
		if break_flag: break
	return min_err
	

def ave_ali_err_MPI(stack):
	from utilities import inverse_transform2, amoeba, get_params2D
	from math import sqrt
	from utilities import reduce_EMData_to_root, print_msg
	from mpi import mpi_comm_size, mpi_comm_rank, mpi_bcast, mpi_reduce, MPI_COMM_WORLD, MPI_FLOAT, MPI_MIN
	from random import random

	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid = mpi_comm_rank(MPI_COMM_WORLD)
	main_node = 0

	nima = EMUtil.get_image_count(stack)
	v1 = []
	v2 = []
	mirror_same = 0 
	for im in xrange(nima):
		img = EMData()
		img.read_image(stack, im)
		alpha, sx, sy, mirror, mirror = get_params2D(img)
		v1.append(alpha)
		v1.append(sx)
		v1.append(sy)
		v1.append(mirror)
		alpha_i = img.get_attr("alpha_i")
		sx_i = img.get_attr("sx_i")
		sy_i = img.get_attr("sy_i")
		mirror_i = img.get_attr("mirror_i")
		if mirror==mirror_i:	mirror_same += 1
		alpha_i2, sx_i2, sy_i2, scale2 = inverse_transform2(alpha_i, sx_i, sy_i)
		v2.append(alpha_i2)
		v2.append(sx_i2)
		v2.append(sy_i2)
		v2.append(mirror_i)

	same_rate = float(mirror_same)/nima
	mirror_flip = False
	if same_rate < 0.5:
		mirror_flip = True
		for im in xrange(nima):
			v2[im*4+3]=1-v2[im*4+3]
		mirror_same = nima-mirror_same
		same_rate = 1-same_rate
	
	data = []
	data.append(v1)
	data.append(v2)
	data.append(nima)
	data.append(mirror_same)
	data.append(mirror_flip)

	ic = 0
	min_err = 1e10
	trial = max(20/number_of_proc, 1)
	for i in xrange(trial):
		alpha = random()*360.0
		sx = random()*6.0-3.0
		sy = random()*6.0-3.0
		if i==0 and myid==0: args = [0.0, 0.0, 0.0]
		else: args = [alpha, sx, sy]
		ps = amoeba(args, [1.0, 1.0, 1.0], err_func, 1.e-5, 1.e-5, 1000, data)
		err = -ps[1]
		if err < min_err:	min_err = err
	min_err = mpi_reduce(min_err, 1, MPI_FLOAT, MPI_MIN, main_node, MPI_COMM_WORLD)
	if myid==main_node:	min_err = min_err[0]
	min_err = mpi_bcast(min_err, 1, MPI_FLOAT, main_node, MPI_COMM_WORLD)
	min_err = min_err[0]
	return min_err
	
	
"""
def gridrot_shift2D(image, kb, ang = 0.0, sx = 0.0, sy = 0.0):
	from math import pi, sin, cos
	
	N = image.get_ysize()
	image1 = image.copy()
	image1 = image1.fouriergridrot2d(ang, 1.0, kb)
	image1.center_origin_fft()
	for x in xrange((N+2)/2):
		for y in xrange(N):
			if y > N/2-1: yy = y-N
			else: yy = y
			Re = image1.get_value_at(x*2,y)
			Im = image1.get_value_at(x*2+1,y)
			ang = -2*pi*(sx*x+sy*yy)/N
			image1.set_value_at(x*2, y, Re*cos(ang)-Im*sin(ang)) 
			image1.set_value_at(x*2+1, y, Re*sin(ang)+Im*cos(ang))
	return image1
"""
	
def SSNR_func(args, data):
	from utilities import print_msg
	
	img_data = data[0]
	nima = data[1]
	maskI = data[2]
	kb = data[3]
	CTF = data[6]
	SSNR_fit = data[7]
	if CTF:
		index_list = data[8]
		ctfimg_list = data[9]
		ctfimg2 = data[10]
		ctf_data = 3
	else:
		ctf_data = 0
	if SSNR_fit:
		SSNR_img = data[8+ctf_data]
		SSNR_sig = data[9+ctf_data]
		
	N = img_data[0].get_ysize()
	avgimg  = EMData(N, N, 1, False)
	var     = EMData(N, N, 1, False)
	
	for im in xrange(nima):
		imgft = img_data[im].copy()
		alpha = args[im*3]
		sx = args[im*3+1]
		sy = args[im*3+2]
		#imgft = gridrot_shift2D(imgft, kb, alpha, sx, sy)
		imgft = imgft.fouriergridrot_shift2d(alpha, sx, sy, kb)
		imgft.center_origin_fft()
		Util.add_img2(var, imgft)
		if CTF:
			ctfimg = ctfimg_list[index_list[im]]
			Util.mul_img(imgft, ctfimg)
		Util.add_img(avgimg, imgft)	

	if CTF:
		Util.div_filter(avgimg, ctfimg2)
	else:
		Util.mul_scalar(avgimg, 1.0/float(nima))		
	avgimg_2 = avgimg.copy()
	Util.mul_img(avgimg_2, avgimg_2.conjg())
	if CTF:
		Util.mul_img(avgimg_2, ctfimg2)
	else:
		Util.mul_scalar(avgimg_2, float(nima))
	Util.sub_img(var, avgimg_2)
	Util.mul_scalar(var, 1.0/float(nima-1))
	
	SSNR = avgimg_2.copy()
	Util.div_filter(SSNR, var)
	
	a0 = Util.infomask(SSNR, maskI, True)
	sum_SSNR = a0[0]
	print_msg("SSNR = %20.7f\n"%(sum_SSNR))
	
	if SSNR_fit:
		beta = 10.0
		Util.sub_img(SSNR, maskI)
		SSNR = SSNR.process("threshold.belowtozero", {"minval": 0.0})
		Util.sub_img(SSNR, SSNR_img)
		Util.div_filter(SSNR, SSNR_sig)
		Util.mul_img(SSNR, SSNR)
		a0 = Util.infomask(SSNR, maskI, True)
		sum_SSNR -= beta*a0[0]
	
	return -sum_SSNR


def SSNR_grad(args, data):
	from numpy import zeros, array, float64

	img_data = data[0]
	nima = data[1]
	maskI = data[2]
	kb = data[3]
	_jX = data[4]
	_jY = data[5]
	CTF = data[6]
	SSNR_fit = data[7]
	if CTF:
		index_list = data[8]
		ctfimg_list = data[9]
		ctfimg2 = data[10]
		ctf_data = 3
	else:
		ctf_data = 0
	if SSNR_fit:
		SSNR_img = data[8+ctf_data]
		SSNR_sig = data[9+ctf_data]
	
	N = img_data[0].get_ysize()
	avgimg  = EMData(N, N, 1, False)
	var     = EMData(N, N, 1, False)
	img_data_new = []
	d_img = []

	for im in xrange(nima):
		imgft = img_data[im].copy()
		alpha = args[im*3]
		sx = args[im*3+1]
		sy = args[im*3+2]
		
		dalpha = 0.05
		#imgft0 = gridrot_shift2D(imgft, kb, alpha, sx, sy)
		#imgft1 = gridrot_shift2D(imgft, kb, alpha-dalpha, sx, sy)
		#imgft2 = gridrot_shift2D(imgft, kb, alpha+dalpha, sx, sy)
		imgft0 = imgft.fouriergridrot_shift2d(alpha, sx, sy, kb)
		imgft0.center_origin_fft()
		imgft1 = imgft.fouriergridrot_shift2d(alpha-dalpha, sx, sy, kb)
		imgft1.center_origin_fft()
		imgft2 = imgft.fouriergridrot_shift2d(alpha+dalpha, sx, sy, kb)
		imgft2.center_origin_fft()
		Util.sub_img(imgft2, imgft1)
		Util.mul_scalar(imgft2, 1/(2*dalpha))
				
		img_data_new.append(imgft0)
		d_img.append(imgft2)
		Util.add_img2(var, imgft0)
		if CTF:
			ctfimg = ctfimg_list[index_list[im]]
			Util.mul_img(imgft0, ctfimg)
		Util.add_img(avgimg, imgft0)
		
	if CTF:
		Util.div_filter(avgimg, ctfimg2)
	else:
		Util.mul_scalar(avgimg, 1.0/float(nima))
	avgimg_2 = avgimg.copy()
	Util.mul_img(avgimg_2, avgimg_2.conjg())
	if CTF:
		Util.mul_img(avgimg_2, ctfimg2)
	else:
		Util.mul_scalar(avgimg_2, float(nima))
	Util.sub_img(var, avgimg_2)
	Util.mul_scalar(var, 1.0/float(nima-1))
	
	avgimg_conj = avgimg.conjg()
	dSSNR = avgimg_conj.copy()
	Util.div_filter(dSSNR, var)

	if SSNR_fit:
		beta = 10.0
		SSNR = avgimg_2.copy()
		Util.div_filter(SSNR, var)
		Util.sub_img(SSNR, maskI)
		SSNR = SSNR.process("threshold.belowtozero", {"minval": 0.0})
		Util.sub_img(SSNR, SSNR_img)
		Util.div_filter(SSNR, SSNR_sig)
		Util.div_filter(SSNR, SSNR_sig)
		Util.mul_scalar(SSNR, 2*beta)
		C = maskI.copy()
		Util.sub_img(C, SSNR)
		Util.mul_img(dSSNR, C)
	
	g = zeros(args.shape, float64)
	for im in xrange(nima):
		img_new = img_data_new[im].copy()

		dSSNR_copy = dSSNR.copy()
		Util.mul_img(dSSNR_copy, d_img[im])
		if CTF:
			Util.mul_img(dSSNR_copy, ctfimg_list[index_list[im]])
		Util.add_img(dSSNR_copy, dSSNR_copy.conjg())
		a0 = Util.infomask(dSSNR_copy, maskI, True)
		g[im*3] = -a0[0]
		
		dSSNR_copy = dSSNR.copy()
		Util.mul_img(dSSNR_copy, img_new)
		if CTF:
			Util.mul_img(dSSNR_copy, ctfimg_list[index_list[im]])
		dSSNR_fft = dSSNR_copy.copy()		
		Util.mul_img(dSSNR_fft, _jX)
		Util.add_img(dSSNR_fft, dSSNR_fft.conjg())
		a0 = Util.infomask(dSSNR_fft, maskI, True)
		g[im*3+1] = -a0[0]
		
		dSSNR_fft = dSSNR_copy.copy()		
		Util.mul_img(dSSNR_fft, _jY)
		Util.add_img(dSSNR_fft, dSSNR_fft.conjg())
		a0 = Util.infomask(dSSNR_fft, maskI, True)
		g[im*3+2] = -a0[0]
	return g


def SSNR_func_MPI(args, data):
	from applications import MPI_start_end
	from utilities import reduce_EMData_to_root, print_msg
	from mpi import mpi_comm_size, mpi_comm_rank, mpi_bcast, MPI_COMM_WORLD, MPI_FLOAT

	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid = mpi_comm_rank(MPI_COMM_WORLD)
	main_node = 0

	img_data = data[0]
	nima = data[1]
	maskI = data[2]
	kb = data[3]
	CTF = data[6]
	SSNR_fit = data[7]
	if CTF:
		index_list = data[8]
		ctfimg_list = data[9]
		ctfimg2 = data[10]
		ctf_data = 3
	else:
		ctf_data = 0
	if SSNR_fit:
		"""
		SSNR_img = data[8+ctf_data]
		SSNR_sig = data[9+ctf_data]
		"""
		SSNR_r = data[8+ctf_data]
	
	image_start, image_end = MPI_start_end(nima, number_of_proc, myid)
	
	N = img_data[0].get_ysize()
	avgimg  = EMData(N, N, 1, False)
	var     = EMData(N, N, 1, False)

	for im in xrange(image_start, image_end):
		imgft = img_data[im-image_start].copy()
		alpha = args[im*3]
		sx = args[im*3+1]
		sy = args[im*3+2]
		#imgft = gridrot_shift2D(imgft, kb, alpha, sx, sy)			
		imgft = imgft.fouriergridrot_shift2d(alpha, sx, sy, kb)
		imgft.center_origin_fft()
		Util.add_img2(var, imgft)
		if CTF:
			ctfimg = ctfimg_list[index_list[im]]
			Util.mul_img(imgft, ctfimg)
		Util.add_img(avgimg, imgft)
		
	reduce_EMData_to_root(avgimg, myid, main_node)
	reduce_EMData_to_root(var, myid, main_node)
	if myid == main_node:
		if CTF:
			Util.div_filter(avgimg, ctfimg2)
		else:
			Util.mul_scalar(avgimg, 1.0/float(nima))
		avgimg_2 = avgimg.copy()
		Util.mul_img(avgimg_2, avgimg_2.conjg())
		if CTF:
			Util.mul_img(avgimg_2, ctfimg2)
		else:
			Util.mul_scalar(avgimg_2, float(nima))
		Util.sub_img(var, avgimg_2)
		Util.mul_scalar(var, 1.0/float(nima-1))
	
		SSNR = avgimg_2.copy()
		Util.div_filter(SSNR, var)
		
		a0 = Util.infomask(SSNR, maskI, True)
		sum_SSNR = a0[0]
		print_msg("SSNR = %20.7f\n"%(sum_SSNR))
		if SSNR_fit:
			from fundamentals import rot_avg_table
			beta = 1.0
			avgimg_2 = Util.pack_complex_to_real(avgimg_2)
			var   = Util.pack_complex_to_real(var)
			ravgimg_2 = rot_avg_table(avgimg_2)
			rvar = rot_avg_table(var)
			SSNR_diff = 0.0
			for i in xrange(N/2+1):
				qt = max(0.0, ravgimg_2[i]/rvar[i] - 1.0)
				diff = (qt-SSNR_r[i])/max(1.0, SSNR_r[i])
				SSNR_diff += diff**2
			sum_SSNR -= beta*SSNR_diff
				
			"""
			Util.sub_img(SSNR, maskI)
			SSNR = SSNR.process("threshold.belowtozero", {"minval": 0.0})
			Util.sub_img(SSNR, SSNR_img)
			Util.div_filter(SSNR, SSNR_sig)
			Util.mul_img(SSNR, SSNR)
			a0 = Util.infomask(SSNR, maskI, True)
			sum_SSNR -= beta*a0[0]
			"""
		#print "After:  SSNR=", sum_SSNR
	else: 	
		sum_SSNR = 0.0
	
	sum_SSNR = mpi_bcast(sum_SSNR, 1, MPI_FLOAT, main_node, MPI_COMM_WORLD)
	return -sum_SSNR[0]


def SSNR_grad_MPI(args, data):
	from numpy import zeros, array, float32, float64
	from applications import MPI_start_end
	from utilities import reduce_EMData_to_root, bcast_EMData_to_all 
	from utilities import reduce_array_to_root, bcast_array_to_all
	from mpi import mpi_comm_size, mpi_comm_rank, mpi_bcast, MPI_COMM_WORLD, MPI_FLOAT

	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid = mpi_comm_rank(MPI_COMM_WORLD)
	main_node = 0

	img_data = data[0]
	nima = data[1]
	maskI = data[2]
	kb = data[3]
	_jX = data[4]
	_jY = data[5]
	CTF = data[6]
	SSNR_fit = data[7]
	if CTF:
		index_list = data[8]
		ctfimg_list = data[9]
		ctfimg2 = data[10]
		ctf_data = 3
	else:
		ctf_data = 0
	if SSNR_fit:
		"""
		SSNR_img = data[8+ctf_data]
		SSNR_sig = data[9+ctf_data]
		"""
		SSNR_r = data[8+ctf_data]
	
	image_start, image_end = MPI_start_end(nima, number_of_proc, myid)

	N = img_data[0].get_ysize()
	avgimg  = EMData(N, N, 1, False)
	var     = EMData(N, N, 1, False)
	img_data_new = []
	d_img = []

	for im in xrange(image_start, image_end):
		imgft = img_data[im-image_start].copy()
		alpha = args[im*3]
		sx = args[im*3+1]
		sy = args[im*3+2]
		
		dalpha = 0.05
		#imgft0 = gridrot_shift2D(imgft, kb, alpha, sx, sy)
		#imgft1 = gridrot_shift2D(imgft, kb, alpha-dalpha, sx, sy)
		#imgft2 = gridrot_shift2D(imgft, kb, alpha+dalpha, sx, sy)
		imgft0 = imgft.fouriergridrot_shift2d(alpha, sx, sy, kb)
		imgft0.center_origin_fft()		
		imgft1 = imgft.fouriergridrot_shift2d(alpha-dalpha, sx, sy, kb)
		imgft1.center_origin_fft()
		imgft2 = imgft.fouriergridrot_shift2d(alpha+dalpha, sx, sy, kb)
		imgft2.center_origin_fft()
		Util.sub_img(imgft2, imgft1)
		Util.mul_scalar(imgft2, 1/(2*dalpha))
				
		img_data_new.append(imgft0)
		d_img.append(imgft2)
		Util.add_img2(var, imgft0)
		if CTF:
			ctfimg = ctfimg_list[index_list[im]]
			Util.mul_img(imgft0, ctfimg)
		Util.add_img(avgimg, imgft0)
		
	reduce_EMData_to_root(avgimg, myid, main_node)
	reduce_EMData_to_root(var, myid, main_node)
	bcast_EMData_to_all(avgimg, myid, main_node)
	bcast_EMData_to_all(var, myid, main_node)

	if CTF:
		Util.div_filter(avgimg, ctfimg2)
	else:
		Util.mul_scalar(avgimg, 1.0/float(nima))
	avgimg_2 = avgimg.copy()
	Util.mul_img(avgimg_2, avgimg_2.conjg())
	if CTF:
		Util.mul_img(avgimg_2, ctfimg2)
	else:
		Util.mul_scalar(avgimg_2, float(nima))
	Util.sub_img(var, avgimg_2)
	Util.mul_scalar(var, 1.0/float(nima-1))
	
	avgimg_conj = avgimg.conjg()
	dSSNR = avgimg_conj.copy()
	Util.div_filter(dSSNR, var)

	if SSNR_fit:
		from fundamentals import rot_avg_table
		from math import sqrt, pi
		beta = 1.0
		avgimg_2 = Util.pack_complex_to_real(avgimg_2)
		var   = Util.pack_complex_to_real(var)
		ravgimg_2 = rot_avg_table(avgimg_2)
		rvar = rot_avg_table(var)
		C = EMData(N, N, 1, False)
		S = pi*(0.49*N)**2
		for x in xrange((N+2)/2):
			for y in xrange(N):
 				if y > N/2-1: yy = y-N
				else: yy = y
				r = sqrt(x**2+yy**2)
				if r < 0.49*N:
					i = int(r+0.5)
					qt = max(0.0, ravgimg_2[i]/rvar[i] - 1.0)
					temp = 1-2*beta*(qt-SSNR_r[i])/max(1.0, SSNR_r[i])**2*S/max(1, 2*pi*i)
					C.set_value_at(x*2, y, temp)
		Util.mul_img(dSSNR, C)
		
		"""
		SSNR = avgimg_2.copy()
		Util.div_filter(SSNR, var)
		Util.sub_img(SSNR, maskI)
		SSNR = SSNR.process("threshold.belowtozero", {"minval": 0.0})
		Util.sub_img(SSNR, SSNR_img)
		Util.div_filter(SSNR, SSNR_sig)
		Util.div_filter(SSNR, SSNR_sig)
		Util.mul_scalar(SSNR, 2*beta)
		C = maskI.copy()
		Util.sub_img(C, SSNR)
		Util.mul_img(dSSNR, C)
		"""
	
	h = zeros(args.shape, float32)
	for im in xrange(image_start, image_end):
		img_new = img_data_new[im-image_start].copy()

		dSSNR_copy = dSSNR.copy()
		Util.mul_img(dSSNR_copy, d_img[im-image_start])
		if CTF:
			Util.mul_img(dSSNR_copy, ctfimg_list[index_list[im]])
		Util.add_img(dSSNR_copy, dSSNR_copy.conjg())
		a0 = Util.infomask(dSSNR_copy, maskI, True)
		h[im*3] = -a0[0]
		
		dSSNR_copy = dSSNR.copy()
		Util.mul_img(dSSNR_copy, img_new)
		if CTF:
			Util.mul_img(dSSNR_copy, ctfimg_list[index_list[im]])
		
		dSSNR_fft = dSSNR_copy.copy()		
		Util.mul_img(dSSNR_fft, _jX)
		Util.add_img(dSSNR_fft, dSSNR_fft.conjg())
		a0 = Util.infomask(dSSNR_fft, maskI, True)
		h[im*3+1] = -a0[0]
		
		dSSNR_fft = dSSNR_copy.copy()		
		Util.mul_img(dSSNR_fft, _jY)
		Util.add_img(dSSNR_fft, dSSNR_fft.conjg())
		a0 = Util.infomask(dSSNR_fft, maskI, True)
		h[im*3+2] = -a0[0]
		
	reduce_array_to_root(h, myid, main_node)
	bcast_array_to_all(h, myid, main_node)
	
	g = zeros(args.shape, float64)
	g = float64(h)
	return g


def ali_SSNR(stack, maskfile=None, ou=-1, maxit=10, CTF=False, opti_method="CG", SSNR_fit=False, SSNR=[], MPI=False):

	if MPI:
		ali_SSNR_MPI(stack, maskfile, ou, maxit, CTF, opti_method, SSNR_fit, SSNR)
		return
		
	from math import pi, sqrt
	from fundamentals import fftip
	from numpy import Inf
	from scipy.optimize.lbfgsb import fmin_l_bfgs_b
	from scipy.optimize.optimize import fmin_cg
	from utilities import getImage, get_params2D, set_params2D, print_begin_msg, print_end_msg, print_msg
	
	if CTF:
		from utilities import get_arb_params
		from morphology import ctf_img

	print_begin_msg("ali_SSNR")

	if opti_method!="CG" and opti_method!="LBFGSB":
		 print "Unknown optimization method!"
		 return
		 
	nima = EMUtil.get_image_count(stack)
	ima = EMData()
	ima.read_image(stack, 0)
	nx = ima.get_xsize()
	
	last_ring = int(ou);	max_iter = int(maxit)
	if last_ring == -1:	last_ring = nx//2-2
	
	print_msg("Input stack                 : %s\n"%(stack))
	print_msg("Outer radius                : %i\n"%(last_ring))
	print_msg("Maximum iteration           : %i\n"%(max_iter))
	print_msg("Data with CTF               : %s\n"%(CTF))
	print_msg("Optimization method         : %s\n"%(opti_method))

	if maskfile:
		import  types
		if type(maskfile) is types.StringType:  
			print_msg("Maskfile                    : %s\n\n"%(maskfile))
			mask = getImage(maskfile)
		else:
			print_msg("Maskfile                    : user provided in-core mask\n\n")
			mask = maskfile
	else : 
		print_msg("Maskfile                    : default, a circle with radius %i\n\n"%(last_ring))
		mask = model_circle(last_ring,nx,nx)
	
	
	# prepare kb for gridding interpolation
	npad = 2
	N = nx*npad
	K = 6
	alpha = 1.75
	r = nx/2
	v = K/2.0/N
	kb = Util.KaiserBessel(alpha, K, r, v, N)
	del alpha, K, r, v

	# generate the mask in Fourier space
	maskI = EMData(N, N, 1, False)
	for x in xrange((N+2)/2):
		for y in xrange(N):
 			if y > N/2-1: yy = y-N
			else: yy = y
			if x**2+yy**2 < (N*0.49)**2:
				maskI.set_value_at(x*2, y, 1) 
	maskI.set_value_at(0, 0, 0)
	maskI.set_value_at(1, 0, 0)
	
	if CTF:
		parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor", "ctf_applied"]
		defocus_list = []
		ctfimg_list = []
		index_list = []
		ctfimg2 = EMData(N, N, 1, False)

	# There two matrixes in Fourier space is necessary for calculating derivatives
	_jX = EMData(N, N, 1, False)
	_jY = EMData(N, N, 1, False)
	for x in xrange((N+2)/2):
		for y in xrange(N):
 			if y > N/2-1: yy = y-N
			else: yy = y
		 	_jX.set_value_at(x*2+1, y, -x*2*pi/N) 
 			_jY.set_value_at(x*2+1, y, -yy*2*pi/N) 

	img_data= []
	x0 = [0.0]*(nima*3)	
	if opti_method == "LBFGSB":	bounds = []

	# pre-processing, get initial parameters and boundaries (for LBFGSB)
	for im in xrange(nima):
		if im>0:
			ima = EMData()
			ima.read_image(stack, im)
		if CTF:
			ctf_params = get_arb_params(ima, parnames)
		st = Util.infomask(ima, mask, False)
		ima -= st[0]	
		ima.divkbsinh(kb)
		ima = ima.norm_pad(False, npad)
		fftip(ima)
		ima.center_origin_fft()
		img_data.append(ima)
		if CTF:
			if not (ctf_params[1] in defocus_list):
				defocus_list.append(ctf_params[1])
				ctfimg = ctf_img(N, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5], ny = N, nz = 1)
				ctfimg_list.append(ctfimg)
				index_list.append(len(defocus_list)-1)
			else:
				index = defocus_list.index(ctf_params[1])
				ctfimg = ctfimg_list[index]
				index_list.append(index)
			Util.add_img2(ctfimg2, ctfimg)			

		x0[im*3], x0[im*3+1], x0[im*3+2], dummy1, dummy2 = get_params2D(ima)
		if opti_method == "LBFGSB":
			bounds.append((x0[im*3]-2.0, x0[im*3]+2.0))
			bounds.append((x0[im*3+1]-1.0, x0[im*3+1]+1.0))
			bounds.append((x0[im*3+2]-1.0, x0[im*3+2]+1.0))

	# Use a gradient method here
	data = []
	data.append(img_data)
	data.append(nima)
	data.append(maskI)
	data.append(kb)
	data.append(_jX)
	data.append(_jY)
	data.append(CTF)
	data.append(SSNR_fit)

	if CTF:
		data.append(index_list)
		data.append(ctfimg_list)
		data.append(ctfimg2)
	if SSNR_fit:
		"""
		SSNR_img = EMData(N, N, 1, False)
		SSNR_sig = EMData(N, N, 1, False)
		for x in xrange((N+2)/2):
			for y in xrange(N):
 				if y > N/2-1: yy = y-N
				else: yy = y
				r = sqrt(x**2+yy**2)
				if r < N*0.49:
					i = int(r/2)
					j = r/2-i
					temp = (SSNR[i]*(1-j)+SSNR[i+1]*j)*nima
					SSNR_img.set_value_at(x*2, y, temp) 
					if temp < 1.0: temp = 1.0
					SSNR_sig.set_value_at(x*2, y, temp)					
		data.append(SSNR_img)
		data.append(SSNR_sig)
		"""
		SSNR_r = []
		for i in xrange(N/2+1):
			if i%2==0: SSNR_r.append(SSNR[i/2]*nima)
			else:	SSNR_r.append((SSNR[i/2]+SSNR[i/2+1])*0.5*nima)
		data.append(SSNR_r)
	
	if opti_method == "CG":
		ps = fmin_cg(SSNR_func, x0, fprime=SSNR_grad, args=([data]), gtol=1e-3, norm=Inf, epsilon=1e-5,
        	      maxiter=max_iter, full_output=0, disp=0, retall=0, callback=None)		
	else:		
		ps, val, d = fmin_l_bfgs_b(SSNR_func, x0, args=[data], fprime=SSNR_grad, bounds=bounds, m=10, 
			factr=1e3, pgtol=1e-4, epsilon=1e-2, iprint=-1, maxfun=max_iter)
	
	# write the result into the header
	for im in xrange(nima):
		ima = EMData()
		ima.read_image(stack, im)
		set_params2D(ima, [ps[im*3], ps[im*3+1], ps[im*3+2], 0, 1.0])
		ima.write_image(stack, im)	

	print_end_msg("ali_SSNR")


def ali_SSNR_MPI(stack, maskfile=None, ou=-1, maxit=10, CTF=False, opti_method="CG", SSNR_fit=False, SSNR=[]):

	from applications import MPI_start_end
	from math import pi, sqrt
	from fundamentals import fftip
	from numpy import Inf
	from scipy.optimize.lbfgsb import fmin_l_bfgs_b
	from scipy.optimize.optimize import fmin_cg
	from mpi import mpi_comm_size, mpi_comm_rank, mpi_bcast, MPI_COMM_WORLD
	from utilities import getImage, set_params2D, get_params2D, print_begin_msg, print_end_msg, print_msg
	
	if CTF:
		from utilities import get_arb_params
		from morphology import ctf_img

	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid = mpi_comm_rank(MPI_COMM_WORLD)
	main_node = 0
	
	if myid == main_node:	print_begin_msg("ali_SSNR_MPI")

	if opti_method!="CG" and opti_method!="LBFGSB":
		 print "Wrong optimization method!"
		 return
		 
	nima = EMUtil.get_image_count(stack)
	image_start, image_end = MPI_start_end(nima, number_of_proc, myid)
	ima = EMData()
	ima.read_image(stack, 0)
	nx = ima.get_xsize()
	
	last_ring = int(ou);	max_iter = int(maxit)
	if last_ring == -1:	last_ring = nx//2-2
	
	if myid == main_node:
		print_msg("Input stack                 : %s\n"%(stack))
		print_msg("Outer radius                : %i\n"%(last_ring))
		print_msg("Maximum iteration           : %i\n"%(max_iter))
		print_msg("Data with CTF               : %s\n"%(CTF))
		print_msg("Optimization method         : %s\n"%(opti_method))
		print_msg("Number of processors used   : %d\n"%(number_of_proc))

	if maskfile:
		import  types
		if type(maskfile) is types.StringType:  
			if myid == main_node:		print_msg("Maskfile                    : %s\n\n"%(maskfile))
			mask = getImage(maskfile)
		else:
			if myid == main_node: 		print_msg("Maskfile                    : user provided in-core mask\n\n")
			mask = maskfile
	else : 
		if myid==main_node: 	print_msg("Maskfile                    : default, a circle with radius %i\n\n"%(last_ring))
		mask = model_circle(last_ring, nx, nx)
	
	
	# prepare kb for gridding interpolation
	npad = 2
	N = nx*npad
	K = 6
	alpha = 1.75
	r = nx/2
	v = K/2.0/N
	kb = Util.KaiserBessel(alpha, K, r, v, N)
	del alpha, K, r, v

	# generate the mask in Fourier space
	maskI = EMData(N, N, 1, False)
	for x in xrange((N+2)/2):
		for y in xrange(N):
 			if y > N/2-1: yy = y-N
			else: yy = y
			if x**2+yy**2 < (N*0.49)**2:
				maskI.set_value_at(x*2, y, 1) 
	maskI.set_value_at(0, 0, 0)
	maskI.set_value_at(1, 0, 0)
	
	if CTF:
		parnames = ["Pixel_size", "defocus", "voltage", "Cs", "amp_contrast", "B_factor"]
		defocus_list = []
		ctfimg_list = []
		index_list = []
		ctfimg2 = EMData(N, N, 1, False)

	# There two matrixes in Fourier space is necessary for calculating derivatives
	_jX = EMData(N, N, 1, False)
	_jY = EMData(N, N, 1, False)
	for x in xrange((N+2)/2):
		for y in xrange(N):
 			if y > N/2-1: yy = y-N
			else: yy = y
		 	_jX.set_value_at(x*2+1, y, -x*2*pi/N) 
 			_jY.set_value_at(x*2+1, y, -yy*2*pi/N) 

	img_data= []
	x0 = [0.0]*(nima*3)	
	if opti_method == "LBFGSB":	bounds = []

	# pre-processing, get initial parameters and boundaries (for LBFGSB)
	for im in xrange(nima):
		if im>0:
			ima = EMData()
			ima.read_image(stack, im)
		if CTF:
			ctf_params = get_arb_params(ima, parnames)
		if (im >= image_start) and (im < image_end):
			st = Util.infomask(ima, mask, False)
			ima -= st[0]	
			ima.divkbsinh(kb)
			ima = ima.norm_pad(False, npad)
			fftip(ima)
			ima.center_origin_fft()
			img_data.append(ima)
		if CTF:
			if not (ctf_params[1] in defocus_list):
				defocus_list.append(ctf_params[1])
				ctfimg = ctf_img(N, ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5], ny = N, nz = 1)
				ctfimg_list.append(ctfimg)
				index_list.append(len(defocus_list)-1)
			else:
				index = defocus_list.index(ctf_params[1])
				ctfimg = ctfimg_list[index]
				index_list.append(index)
			Util.add_img2(ctfimg2, ctfimg)			
		
		x0[im*3], x0[im*3+1], x0[im*3+2], dummy1, dummy2 = get_params2D(ima)
		if opti_method == "LBFGSB":
			bounds.append((x0[im*3]-2.0, x0[im*3]+2.0))
			bounds.append((x0[im*3+1]-1.0, x0[im*3+1]+1.0))
			bounds.append((x0[im*3+2]-1.0, x0[im*3+2]+1.0))

	# Use a gradient method here
	data = []
	data.append(img_data)
	data.append(nima)
	data.append(maskI)
	data.append(kb)
	data.append(_jX)
	data.append(_jY)
	data.append(CTF)
	data.append(SSNR_fit)

	if CTF:
		data.append(index_list)
		data.append(ctfimg_list)
		data.append(ctfimg2)
	if SSNR_fit:
		"""
		SSNR_img = EMData(N, N, 1, False)
		SSNR_sig = EMData(N, N, 1, False)
		for x in xrange((N+2)/2):
			for y in xrange(N):
 				if y > N/2-1: yy = y-N
				else: yy = y
				r = sqrt(x**2+yy**2)
				if r < N*0.49:
					i = int(r/2)
					j = r/2-i
					temp = (SSNR[i]*(1-j)+SSNR[i+1]*j)*nima
					SSNR_img.set_value_at(x*2, y, temp) 
					if temp < 1.0: temp = 1.0
					SSNR_sig.set_value_at(x*2, y, temp)					
		data.append(SSNR_img)
		data.append(SSNR_sig)
		"""
		SSNR_r = []
		for i in xrange(N/2+1):
			if i%2==0: SSNR_r.append(SSNR[i/2]*nima)
			else:	SSNR_r.append((SSNR[i/2]+SSNR[i/2+1])*0.5*nima)
		data.append(SSNR_r)
	
	if opti_method == "CG":
		ps = fmin_cg(SSNR_func_MPI, x0, fprime=SSNR_grad_MPI, args=([data]), gtol=1e-3, norm=Inf, epsilon=1e-5,
        	      maxiter=max_iter, full_output=0, disp=0, retall=0, callback=None)
	else:		
		ps, val, d = fmin_l_bfgs_b(SSNR_func_MPI, x0, args=[data], fprime=SSNR_grad_MPI, bounds=bounds, m=10, 
			factr=1e3, pgtol=1e-4, epsilon=1e-2, iprint=-1, maxfun=max_iter)
	
	# write the result into the header
	if myid == main_node: 
		for im in xrange(nima):
			ima = EMData()
			ima.read_image(stack, im)
			set_params2D(ima, [ps[im*3], ps[im*3+1], ps[im*3+2], 0, 1.0])
			ima.write_image(stack, im)	

	if myid == main_node:	print_end_msg("ali_SSNR_MPI")


###############################################################################################
## GA CLUSTERING ##############################################################################

'''
#-------------------------------------#
| Draft Clustering Genetic Algorithm  |
#-------------------------------------#
'''

def GA_watch(gen, FIT, tstart, msg = None):
	from time      import time, ctime
	from utilities import print_msg

	init = False
	end  = False

	if msg ==  'init':  init = True
	elif msg == 'end':  end = True
	
	if init: f = open('WATCH', 'w')
	else:    f = open('WATCH', 'a')

	max_fit = max(FIT)
	min_fit = min(FIT)
	mean = 0
	for n in range(len(FIT)): mean += FIT[n]
	mean /= len(FIT)
	std  = 0
	for n in xrange(len(FIT)): std += (FIT[n] - mean)**2
	std /= len(FIT)

	if not end:
		#f.write('|gen %5d|  max fit: %11.4e    min fit: %11.4e    mean fit: %11.4e    std fit: %11.4e      %s\n' % (gen, max_fit, min_fit, mean, std, ctime()))
		f.write('|gen %5d|   off-line fit: %11.6e (min)   on-line fit: %11.6e (mean)              %s   %s\n' % (gen, min_fit, mean, ctime(), str(int(time() - tstart)).rjust(8, '0')))
	if gen % 100 == 0 or end:
		#print_msg('|gen %5d|  max fit: %11.4e    min fit: %11.4e    mean fit: %11.4e    std fit: %11.4e      %s\n' % (gen, max_fit, min_fit, mean, std, ctime()))
		print_msg('|gen %5d|   off-line fit: %11.6e (min)   on-line fit: %11.6e (mean)              %s   %s\n' % (gen, min_fit, mean, ctime(), str(int(time() - tstart)).rjust(8, '0')))

	if not end: f.close()

def list_send_im(list, dst):
	from utilities import send_EMData, model_blank
	N    = len(list)
	data = model_blank(N)
	for n in xrange(N): data.set_value_at(n, float(list[n]))
	send_EMData(data, dst, 0)

def list_recv_im(org):
	from utilities import recv_EMData
	data = recv_EMData(org, 0)
	N    = data.get_xsize()
	list = [0] * N
	for n in xrange(N): list[n] = int(data.get_value_at(n))
	return list

# list must be allocated
def list_bcast_im(list, myid, main_node):
	from utilities import bcast_EMData_to_all, model_blank
	N   = len(list)
	data = model_blank(N)
	for n in xrange(N): data.set_value_at(n, float(list[n]))
	bcast_EMData_to_all(data, myid, main_node)
	for n in xrange(N): list[n] = int(data.get_value_at(n))
	return list

def GA(stack, rad, K, sizepop, maxgen, pcross, pmut, pselect, elit = False, POP = None, debug = False, control = False, rand_seed = 10, PART = None, SSE = False, MPI = False):
	from random    import randint, randrange, random, gauss
	from utilities import get_im, model_blank, model_circle
	from utilities import print_begin_msg, print_end_msg, print_msg
	from copy      import deepcopy
	from sys       import exit
	from time      import ctime
	if MPI:
		from statistics_jb import GA_MPI
		GA_MPI(stack, rad, K, sizepop, maxgen, pcross, pmut, pselect, elit, POP, debug, control, rand_seed, PART, SSE)
		return

	seed(rand_seed)

	if POP != None:
		restart = True
		sizepop = len(POP)
	else:
		restart = False
		
	# Informations about images
	image = get_im(stack, 0)
	nx    = image.get_xsize()
	ny    = image.get_ysize()
	N     = EMUtil.get_image_count(stack)
	mask  = model_circle(rad, nx, ny)
	del image

	print_begin_msg('Genetic Algorithm')
	print_msg('Stack name                      : %s\n' % stack)
	print_msg('Number of images                : %i\n' % N)
	print_msg('Number of clusters              : %i\n' % K)
	print_msg('Radius maskfile                 : %d\n' % rad)
	print_msg('Size of population              : %d\n' % sizepop)
	print_msg('Start from new population       : %s\n' % (not restart))
	print_msg('Maximum number of generations   : %d\n' % maxgen)
	print_msg('Crossover rate                  : %f\n' % pcross)
	print_msg('Mutation rate                   : %f\n\n' % pmut)

	# data structure
	if not restart:	POP  = [[] for i in xrange(sizepop)]
	FIT  = [0]    * sizepop
	IM   = [None] * N
	

	# open images
	for n in xrange(N):
		im = get_im(stack, n)
		im = Util.compress_image_mask(im, mask)
		IM[n] = im.copy()

		if n == 0:
			# new params according the mask
			nx    = im.get_xsize()
			ny    = im.get_ysize()
			norm  = nx * ny
			buf   = model_blank(nx,ny)
			maskv = buf.copy()
			maskv.to_one()
	del im

	if not restart:
		# first population (randomly)
		for npop in xrange(sizepop):
			for im in xrange(N):
				POP[npop].append(randint(0, K-1))
	
	# cst for fitness
	cst = buf.copy()
	for n in xrange(N): Util.add_img2(cst, IM[n])
	
	# compute fitness
	for npop in xrange(sizepop):
		tmp        = [0] * K
		ct         = [0] * K
		for k in xrange(K): tmp[k] = buf.copy()

		for im in xrange(N):
			Util.add_img(tmp[POP[npop][im]], IM[im])
			ct[POP[npop][im]] += 1

		val = buf.copy()
		for k in xrange(K):
			if ct[k] != 0: Util.add_img(val, Util.mult_scalar(Util.muln_img(tmp[k], tmp[k]), 1 / float(ct[k])))

		res = Util.subn_img(cst, val)
                ret = Util.infomask(res, maskv, True)
		FIT[npop] = ret[0] / float(norm)

	# loop of generation
	tstart = time()
	for ngen in xrange(maxgen):
		if ngen == 0: GA_watch(ngen, FIT, tstart, 'init')
		else:         GA_watch(ngen, FIT, tstart)

		print 'gen: %6d            %s' % (ngen, ctime())

		# Elitism method
		if elit:
			listfit = []
			for n in xrange(sizepop): listfit.append([FIT[n], n])
			listfit.sort()
			ELIT1     = POP[listfit[0][1]]
			ELIT1_fit = FIT[listfit[0][1]]
			ELIT2     = POP[listfit[1][1]]
			ELIT2_fit = FIT[listfit[1][1]]

		NEWPOP  = [[] for i in xrange(sizepop)]
		NEWFIT  = [0] * sizepop
		
		# select chromosome
		#for nselect in xrange(int(ratio_select * sizepop)):
		for nselect in xrange(int(sizepop/2)):
			
			# Selection Gauss Method
			chr1 = int(min(abs(gauss(0, pselect)), 1.0) * sizepop)
			chr2 = int(min(abs(gauss(0, pselect)), 1.0) * sizepop)
			if chr2 == chr1:    chr2 += 1
			if chr2 >= sizepop: chr2 = 0
			listfit = []
			for n in xrange(sizepop): listfit.append([FIT[n], n])
			listfit.sort()
			chr1 = listfit[chr1][1]
			chr2 = listfit[chr2][1]

					
			# cross-over
			if random() <= pcross:
				s1 = int(random() * N)
								
				child1 = [0] * N
				child2 = [0] * N
				
				child1[0:s1]  = POP[chr1][0:s1]
				child1[s1:N]  = POP[chr2][s1:N]

				child2[0:s1]  = POP[chr2][0:s1]
				child2[s1:N]  = POP[chr1][s1:N]
			else:
				child1 = POP[chr1]
				child2 = POP[chr2]
			

			'''
			# multi-cross-over
			if random() <= pcross:
				nb       = int(random() * N)
				template = []
				child1   = [0] * N
				child2   = [0] * N
				for n in xrange(nb): template.append(int(random() * N))
				for n in xrange(N):
					if n in template:
						child1[n] = POP[chr2][n]
						child2[n] = POP[chr1][n]
					else:
						child1[n] = POP[chr1][n]
						child2[n] = POP[chr2][n]
			else:
				child1 = POP[chr1]
				child2 = POP[chr2]
			'''
								
			
			# mutation child1
			for n in xrange(N):
				if random() <= pmut:
					child1[n] = randrange(0, K)

			# mutation child2
			for n in xrange(N):
				if random() <= pmut:
					child2[n] = randrange(0, K)
								
			# fitness 1
			tmp        = [0] * K
			ct         = [0] * K
			for k in xrange(K): tmp[k] = buf.copy()

			for im in xrange(N):
				Util.add_img(tmp[child1[im]], IM[im])
				ct[child1[im]] += 1

			val = buf.copy()
			for k in xrange(K):
				if ct[k] != 0: Util.add_img(val, Util.mult_scalar(Util.muln_img(tmp[k], tmp[k]), 1 / float(ct[k])))

			res = Util.subn_img(cst, val)
			ret = Util.infomask(res, maskv, True)
			fitchild1 = ret[0] / float(norm)
	 		
			# fitness 2
			tmp        = [0] * K
			ct         = [0] * K
			for k in xrange(K): tmp[k] = buf.copy()

			for im in xrange(N):
				Util.add_img(tmp[child2[im]], IM[im])
				ct[child2[im]] += 1

			val = buf.copy()
			for k in xrange(K):
				if ct[k] != 0: Util.add_img(val, Util.mult_scalar(Util.muln_img(tmp[k], tmp[k]), 1 / float(ct[k])))

			res = Util.subn_img(cst, val)
			ret = Util.infomask(res, maskv, True)
			fitchild2 = ret[0] / float(norm)
		
			# Make new POP
			NEWPOP[2*nselect]     = child1
			NEWPOP[2*nselect + 1] = child2
			NEWFIT[2*nselect]     = fitchild1
			NEWFIT[2*nselect + 1] = fitchild2

		# replace pop by new pop
		POP = deepcopy(NEWPOP)
		del NEWPOP
		FIT = deepcopy(NEWFIT)
		del NEWFIT

		# Elitism method
		if elit:
			listfit = []
			for n in xrange(sizepop): listfit.append([FIT[n], n])
			listfit.sort()
			POP[listfit[-1][1]] = ELIT1
			FIT[listfit[-1][1]] = ELIT1_fit
			POP[listfit[-2][1]] = ELIT2
			FIT[listfit[-2][1]] = ELIT2_fit


	# export result
	best = []
	for n in xrange(sizepop): best.append([FIT[n], n])
	best.sort()
	AVE = [0] * K
	CT  = [0] * K
	for k in xrange(K):
		AVE[k] = buf.copy()
		CT[k]  = 0

	listim = [[] for i in xrange(K)]
	for im in xrange(N):
		Util.add_img(AVE[POP[best[0][1]][im]], IM[im])
		listim[POP[best[0][1]][im]].append(im)
		CT[POP[best[0][1]][im]] += 1
	for k in xrange(K):
		if CT[k] > 0: Util.mul_scalar(AVE[k], 1.0 / float(CT[k]))

	for k in xrange(K):
		AVE[k] = Util.reconstitute_image_mask(AVE[k], mask)
		AVE[k].set_attr('members', listim[k])
		AVE[k].set_attr('nobjects', CT[k])
		AVE[k].write_image('average.hdf', k)

	# Save POP
	import pickle
	f = open('Pop_gen%d' % (ngen+1), 'w')
	pickle.dump(POP, f)
	f.close()

	GA_watch(ngen, FIT, tstart, 'end')

	print_msg('\n')
	print_end_msg('Genetic Algorithm')


def GA_MPI(stack, rad, K, sizepop, maxgen, pcross, pmut, pselect, elit = False, gPOP = None, debug = False, control = False, rand_seed = 10, gPART = None, SSE = False):
	from random     import randint, randrange, random, gauss, seed
	from utilities  import get_im, model_blank, model_circle
	from utilities  import print_begin_msg, print_end_msg, print_msg
	from utilities  import bcast_number_to_all, get_im
	from time       import ctime, time
	from mpi 	import mpi_init, mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	from mpi 	import mpi_reduce, mpi_bcast, mpi_barrier, mpi_recv, mpi_send
	from mpi 	import MPI_SUM, MPI_FLOAT, MPI_INT, MPI_LOR
	import sys

	# ------------------- MPI init ----------------------------- #
	# init
	sys.argv       = mpi_init(len(sys.argv),sys.argv)
	nb_nodes       = mpi_comm_size(MPI_COMM_WORLD)
	myid           = mpi_comm_rank(MPI_COMM_WORLD)
	seed(rand_seed)

	# choose a random node as a main one
	main_node = 0
	if myid  == 0:	main_node = randrange(0, nb_nodes)
	main_node = bcast_number_to_all(main_node,0)
	mpi_barrier(MPI_COMM_WORLD)

	# Informations about images
	image = get_im(stack, 0)
	nx    = image.get_xsize()
	ny    = image.get_ysize()
	N     = EMUtil.get_image_count(stack)
	mask  = model_circle(rad, nx, ny)
	del image

	# Start from new POP?
	if gPOP is None:
		restart   = False
	elif isinstance(gPOP, basestring):
		import pickle
		try:
			f   = open(gPOP, 'r')
			POP = pickle.load(f)
			f.close()
			restart = True
			sizepop = len(POP)
			if myid != main_node: del POP
		except IOError:
			if myid == main_node: print '*** ERROR: file %s not exist' % gPOP
			sys.exit()
	else:
		if myid == main_node: print '*** ERROR: error with POP file name'
		sys.exit()

	# Start from partition?
	if gPART is None:
		flagpart = False
	elif isinstance(gPART, basestring):
		try:
			flagpart = True
			gK  = EMUtil.get_image_count(gPART)
			tmp = [[] for i in xrange(gK)]
			im  = EMData()
			gN  = 0
			for k in xrange(gK):
				im.read_image(gPART, k, True)
				tmp[k] = im.get_attr('members')
				gN += len(tmp[k])
			part = [0] * gN
			for k in xrange(gK):
				for i in tmp[k]: part[int(i)] = k
			if myid != main_node: del part
		except:
			if myid == main_node: print '*** ERROR: error to load partition %s' % gPART
			raise
			sys.exit()
	else:
		if myid == main_node: print '*** ERROR: error with partition name'
		sys.exit()
			
	# Check value
	if sizepop % 2 != 0:
		if myid == main_node: print '*** ERROR: Size of population must be even: %d' % sizepop
		sys.exit()
	elif sizepop < 2 * nb_nodes:
		if myid == main_node: print '*** ERROR: The minimum size of population is %d (2 * nb nodes), actually is %d.' % (nb_nodes * 2, sizepop)
		sys.exit()
	if gPOP is not None and gPART is not None:
		if myid == main_node: print '*** ERROR: Can\'t start from population and partition given in same time, choose one.'
		sys.exit()
	if flagpart and gN != N:
		if myid == main_node: print '*** ERROR: partition and stack file don\'t have the same number of images: %d and %d' % (gN, N)
		sys.exit()
	if flagpart and gK != K:
		if myid == main_node: print '*** ERROR: the value of K=%d and the number of groups in the partition is different: %d' % (K, gK)
		sys.exit()
	
	# number of chromosomes pair per Node
	nsubpop = [0] * nb_nodes
	ct      = 0
	for n in xrange(int(sizepop/2)):
		nsubpop[ct] += 1
		ct          += 1
		if ct >= nb_nodes: ct = 0
		
	i_subpop = [[] for i in xrange(nb_nodes)]
	ct       = 0
	for n in xrange(nb_nodes):
		for i in xrange(nsubpop[n]):
			i_subpop[n].append(ct)
			ct += 1

	if myid == main_node:
		print nsubpop
		print i_subpop

	if myid == main_node:
		start_time = time()
		print_begin_msg('Genetic Algorithm MPI')
		print_msg('Stack name                      : %s\n'   % stack)
		print_msg('Number of images                : %i\n'   % N)
		print_msg('Number of clusters              : %i\n'   % K)
		print_msg('Radius maskfile                 : %d\n'   % rad)
		print_msg('Size of population              : %d\n'   % sizepop)
		print_msg('Number of cpus                  : %d\n'   % nb_nodes)
		print_msg('Start from given population     : %s\n'   % gPOP)
		print_msg('Start from given partition      : %s\n'   % gPART)
		print_msg('Elitism method                  : %s\n'   % elit)
		print_msg('Heuristics (k-means SSE)        : %s\n'   % SSE)
		print_msg('Maximum number of generations   : %d\n'   % maxgen)
		print_msg('Crossover rate                  : %f\n'   % pcross)
		print_msg('Mutation rate                   : %f\n\n' % pmut)

	# data structure
	IM = [None] * N
	if myid == main_node:
		if not restart: POP  = [[] for i in xrange(sizepop)]
		FIT  = [0] * sizepop
	
	# [ALL] open images
	for n in xrange(N):
		im = get_im(stack, n)
		im = Util.compress_image_mask(im, mask)
		IM[n] = im.copy()

		if n == 0:
			# new params according the mask
			nx    = im.get_xsize()
			ny    = im.get_ysize()
			norm  = nx * ny
			buf   = model_blank(nx,ny)
			maskv = buf.copy()
			maskv.to_one()
	del im

	# [ALL] cst for compute the fitness
	cst = buf.copy()
	for n in xrange(N): Util.add_img2(cst, IM[n])

	# [MAIN] create first pop
	if myid == main_node:
		# first population (randomly) or start from given population\
		if not restart: # new POP
			if not flagpart: # no partition given
				for npop in xrange(sizepop):
					for im in xrange(N): POP[npop].append(randint(0, K-1))
			else:
				# duplicate the same chromosome
				for npop in xrange(sizepop): POP[npop] = part
				del part
				
		# [MAIN] compute fitness
		for npop in xrange(sizepop):
			tmp = [0] * K
			ct  = [0] * K
			for k in xrange(K): tmp[k] = buf.copy()

			for im in xrange(N):
				Util.add_img(tmp[POP[npop][im]], IM[im])
				ct[POP[npop][im]] += 1

			val = buf.copy()
			for k in xrange(K):
				if ct[k] != 0: Util.add_img(val, Util.mult_scalar(Util.muln_img(tmp[k], tmp[k]), 1 / float(ct[k])))

			res = Util.subn_img(cst, val)
			ret = Util.infomask(res, maskv, True)
			FIT[npop] = ret[0] / float(norm)

	if debug: MPIlogfile_init(myid)

	## TO WORKS
	#if myid == main_node: print FIT[0]
	#sys.exit()
	if control and myid == main_node: mem_ctrl = ''
	

	# [ALL] loop of generation
	for ngen in xrange(maxgen):
		if debug: MPIlogfile_print(myid, '|start gen %6d|_____________________________%s\n' % (ngen, ctime()))

		# [ALL]
		if debug: MPIlogfile_print(myid, ' ' * 20 + 'Selection:\n')
		if control and myid == main_node:
			f = open('params', 'w')
			f.write('pmut:    %f\n' % pmut)
			f.write('pcross:  %f\n' % pcross)
			f.write('pselect: %f\n' % pselect)
			f.write('_____history_____\n')
			f.write(mem_ctrl)
			f.close()
		
		# [MAIN] logfile
		if myid == main_node:
			
			listchr1 = []
			listchr2 = []
			for npop in xrange(int(sizepop/2)): 
				# [MAIN]
				# Selection Gauss Method
				chr1 = int(min(abs(gauss(0, pselect)), 1.0) * sizepop)
				chr2 = int(min(abs(gauss(0, pselect)), 1.0) * sizepop)
				if chr2 == chr1:    chr2 += 1
				if chr2 >= sizepop: chr2 = 0
				listfit = []
				for n in xrange(sizepop): listfit.append([FIT[n], n])
				listfit.sort()
				if debug: MPIlogfile_print(myid, ' ' * 25 + 'for %d: %d %d' % (npop, chr1, chr2))
				chr1 = listfit[chr1][1]
				chr2 = listfit[chr2][1]
	
				listchr1.append(chr1)
				listchr2.append(chr2)
				
				if debug: MPIlogfile_print(myid, ' #%d #%d\n' % (chr1, chr2))

			# Elitism method
			if elit:
				ELIT1     = POP[listfit[0][1]]
				ELIT1_fit = FIT[listfit[0][1]]
				ELIT2     = POP[listfit[1][1]]
				ELIT2_fit = FIT[listfit[1][1]]
				

		mpi_barrier(MPI_COMM_WORLD)

		# [MAIN] send parents to the others node
		for node in xrange(nb_nodes):
			if myid == main_node and node != main_node:
				for i in i_subpop[node]:
					list_send_im(POP[listchr1[i]], node)
					list_send_im(POP[listchr2[i]], node)
					if debug: MPIlogfile_print(myid, ' ' * 25 + 'parents send to %d\n' % node)

			if myid == node:
				SUBPOP1 = [[] for i in xrange(nsubpop[node])]
				SUBPOP2 = [[] for i in xrange(nsubpop[node])]
				if myid != main_node:
					for i in xrange(nsubpop[node]):
						SUBPOP1[i] = list_recv_im(main_node)
						SUBPOP2[i] = list_recv_im(main_node)
						
						if debug: MPIlogfile_print(myid, ' ' * 25 + 'parents recv from %d\n' % main_node)
				else:
					for i in xrange(nsubpop[node]):
						SUBPOP1[i] = POP[listchr1[node]]
						SUBPOP2[i] = POP[listchr2[node]]
						if debug: MPIlogfile_print(myid, ' ' * 25 + 'parents recv from me\n')

			mpi_barrier(MPI_COMM_WORLD)

		# [MAIN] init new POP
		if myid == main_node:
			POP  = [[0] * N for i in xrange(sizepop)]
			FIT  = [0]  * sizepop

		# loop of subpop for each node
		SUBFIT1 = [0.0] * nsubpop[myid]
		SUBFIT2 = [0.0] * nsubpop[myid]
		for nsub in xrange(nsubpop[myid]):
			parent1 = SUBPOP1[nsub]
			parent2 = SUBPOP2[nsub]

			# [ID] cross-over
			if random() <= pcross:
				s1 = int(random() * N)

				child1 = [0] * N
				child2 = [0] * N

				child1[0:s1] = parent1[0:s1]
				child1[s1:N] = parent2[s1:N]

				child2[0:s1] = parent2[0:s1]
				child2[s1:N] = parent1[s1:N]

				if debug: MPIlogfile_print(myid, ' ' * 20 + 'Cross-over: cross %d\n' % s1)
			else:
				child1 = parent1
				child2 = parent2

				if debug: MPIlogfile_print(myid, ' ' * 20 + 'Cross-over: no cross\n')

			del parent1, parent2

			# [ID] mutation child1
			ct_mut = 0
			for n in xrange(N):
				if random() <= pmut:
					ct_mut += 1
					child1[n] = randrange(0, K)

			if debug: MPIlogfile_print(myid, ' ' * 20 + 'Mutation: child1 %d\n' % ct_mut)

			# [ID] mutation child2
			ct_mut = 0
			for n in xrange(N):
				if random() <= pmut:
					ct_mut += 1
					child2[n] = randrange(0, K)

			if debug: MPIlogfile_print(myid, ' ' * 20 + 'Mutation: child2 %d\n' % ct_mut)

			# [ID] Heuristics child1, k-means SSE
			#if SSE and ngen % 10 == 0:
			if SSE:
				AVE = [0] * K
				CT  = [0] * K
				for k in xrange(K):     AVE[k] = buf.copy()
				for im in xrange(N):
					Util.add_img(AVE[child1[im]], IM[im])
					CT[child1[im]] += 1
				for k in xrange(K):	AVE[k] = Util.mult_scalar(AVE[k], 1.0/float(CT[k]))
				for im in xrange(N):	child1[im] = Util.min_dist(IM[im], AVE)['pos']

			# [ID] Heuristics child2, k-means SSE
			#if SSE and ngen % 10 == 0:
			if SSE:
				AVE = [0] * K
				CT  = [0] * K
				for k in xrange(K):     AVE[k] = buf.copy()
				for im in xrange(N):
					Util.add_img(AVE[child2[im]], IM[im])
					CT[child2[im]] += 1
				for k in xrange(K):	AVE[k] = Util.mult_scalar(AVE[k], 1.0/float(CT[k]))
				for im in xrange(N):	child2[im] = Util.min_dist(IM[im], AVE)['pos']

			# [ID] compute fitness for the child1
			tmp        = [0] * K
			ct         = [0] * K
			for k in xrange(K): tmp[k] = buf.copy()

			for im in xrange(N):
				Util.add_img(tmp[child1[im]], IM[im])
				ct[child1[im]] += 1

			val = buf.copy()
			for k in xrange(K):
				if ct[k] != 0: Util.add_img(val, Util.mult_scalar(Util.muln_img(tmp[k], tmp[k]), 1 / float(ct[k])))

			res = Util.subn_img(cst, val)
			ret = Util.infomask(res, maskv, True)
			fitchild1 = ret[0] / float(norm)

			if debug: MPIlogfile_print(myid, ' ' * 20 + 'Fitness child1: %11.4e\n' % fitchild1)

			# [ID] compute fitness for the child2
			tmp        = [0] * K
			ct         = [0] * K
			for k in xrange(K): tmp[k] = buf.copy()

			for im in xrange(N):
				Util.add_img(tmp[child2[im]], IM[im])
				ct[child2[im]] += 1

			val = buf.copy()
			for k in xrange(K):
				if ct[k] != 0: Util.add_img(val, Util.mult_scalar(Util.muln_img(tmp[k], tmp[k]), 1 / float(ct[k])))

			res = Util.subn_img(cst, val)
			ret = Util.infomask(res, maskv, True)
			fitchild2 = ret[0] / float(norm)

			if debug: MPIlogfile_print(myid, ' ' * 20 + 'Fitness child2: %11.4e\n' % fitchild2)

			# Replacement
			if debug: MPIlogfile_print(myid, ' ' * 20 + 'Replacement:\n')
			SUBPOP1[nsub] = child1
			SUBPOP2[nsub] = child2
			SUBFIT1[nsub] = fitchild1
			SUBFIT2[nsub] = fitchild2
			del child1, child2

		mpi_barrier(MPI_COMM_WORLD)
		
		# [ID] send SUBPOP to main_node
		for node in xrange(nb_nodes):
			if myid == node and myid != main_node:
				for n in xrange(nsubpop[node]):
					list_send_im(SUBPOP1[n], main_node)
					list_send_im(SUBPOP2[n], main_node)
					mpi_send(SUBFIT1[n], 1, MPI_FLOAT, main_node, 1, MPI_COMM_WORLD)
					mpi_send(SUBFIT2[n], 1, MPI_FLOAT, main_node, 1, MPI_COMM_WORLD)
					if debug: MPIlogfile_print(myid, ' ' * 25 + 'childs send to %d\n' % main_node)

			if myid == main_node:
				if node != main_node:
					for i in i_subpop[node]:
						POP[2*i]     = list_recv_im(node)
						POP[2*i + 1] = list_recv_im(node)
						FIT[2*i]     = mpi_recv(1, MPI_FLOAT, node, 1, MPI_COMM_WORLD).tolist()[0]
						FIT[2*i + 1] = mpi_recv(1, MPI_FLOAT, node, 1, MPI_COMM_WORLD).tolist()[0]
						
						if debug: MPIlogfile_print(myid, ' ' * 25 + 'childs recv from %d\n' % node)
				else:
					ct = 0
					for i in i_subpop[node]:
						POP[2*i]     = SUBPOP1[ct]
						POP[2*i + 1] = SUBPOP2[ct]
						FIT[2*i]     = SUBFIT1[ct]
						FIT[2*i + 1] = SUBFIT2[ct]
						ct += 1

						if debug: MPIlogfile_print(myid, ' ' * 25 + 'childs recv from me\n')

			mpi_barrier(MPI_COMM_WORLD)

		del SUBPOP1, SUBPOP2

		# Elitism method, swap the worse by the elit
		if myid == main_node and elit:
			listfit = []
			for n in xrange(sizepop): listfit.append([FIT[n], n])
			listfit.sort()
			POP[listfit[-1][1]] = ELIT1
			FIT[listfit[-1][1]] = ELIT1_fit
			POP[listfit[-2][1]] = ELIT2
			FIT[listfit[-2][1]] = ELIT2_fit

		# logfile
		if myid == main_node:
			if ngen == 0: GA_watch(ngen, FIT, 'init')
			else:         GA_watch(ngen, FIT)

		# TO WORKS
		if control:
			try:
				cmd = open('control', 'r').readline().strip(' \n').split(':')
				if cmd[0] == 'exit':
					#f = open('control', 'w')
					#f.write('')
					#f.close()
					break
				elif cmd[0] == 'pselect':
					pselect = float(cmd[1])
					savecmd = True
				elif cmd[0] == 'pmut':
					pmut    = float(cmd[1])
					savecmd = True
				elif cmd[0] == 'pcross':
					pcross  = float(cmd[1])
					savecmd = True
				elif cmd[0] == 'sse':
					sse     = int(cmd[1])
					savecmd = True
				else:
					savecmd = False

				#f = open('control', 'w')
				#f.write('')
				#f.close()

				if myid == main_node and savecmd: mem_ctrl += 'gen %d: %s %s\n' % (ngen, cmd[0], cmd[1])
				
			except IOError:
				f   = open('control', 'w')
				f.close()
		

	if myid == main_node:
		GA_watch(ngen, FIT, 'end')
		print_msg('\n')
		time_run = int(time() - start_time)
		time_h   = time_run / 3600
		time_m   = (time_run % 3600) / 60
		time_s   = (time_run % 3600) % 60
		print_msg('Time: %s h %s min %s s\n' % (str(time_h).rjust(2, '0'), str(time_m).rjust(2, '0'), str(time_s).rjust(2, '0')))
	if debug: MPIlogfile_end(myid)

	# [MAIN] export result
	if myid == main_node:
		best = []
		for n in xrange(sizepop): best.append([FIT[n], n])
		best.sort()
		AVE = [0] * K
		CT  = [0] * K
		for k in xrange(K):
			AVE[k] = buf.copy()
			CT[k]  = 0

		listim = [[] for i in xrange(K)]
		for im in xrange(N):
			Util.add_img(AVE[POP[best[0][1]][im]], IM[im])
			listim[POP[best[0][1]][im]].append(im)
			CT[POP[best[0][1]][im]] += 1
		for k in xrange(K):
			if CT[k] > 0: Util.mul_scalar(AVE[k], 1.0 / float(CT[k]))

		for k in xrange(K):
			AVE[k] = Util.reconstitute_image_mask(AVE[k], mask)
			AVE[k].set_attr('members', listim[k])
			AVE[k].set_attr('nobjects', CT[k])
			AVE[k].write_image('average.hdf', k)

		# Save POP
		import pickle
		f = open('Pop_gen%d' % (ngen+1), 'w')
		pickle.dump(POP, f)
		f.close()
		
		print_end_msg('Genetic Algorithm MPI')

	mpi_barrier(MPI_COMM_WORLD)
	return

## END GA CLUSTERING ##########################################################################
###############################################################################################



###############################################################################################
## COMMON LINES OLD VERSION ###################################################################

def sinogram2__(image2D):
	from math         import cos,sin
	from fundamentals import fft
	from utilities    import info
	from filter       import filt_tanh
	
	M_PI = 3.141592653589793238462643383279502884197
	
	# prepare 
	M=image2D.get_xsize()
	# padd two times
	npad=2
	N=M*npad
	# support of the window
	K=6
	alpha=1.75
	r=M/2
	v=K/2.0/N

	kb = Util.KaiserBessel(alpha, K, r, K/(2.*N), N)
	
	volft=image2D.average_circ_sub()  	# ASTA - in spider
	
	volft.divkbsinh(kb)		  	# DIVKB2 - in spider
	volft = volft.norm_pad(False, npad)
	volft.do_fft_inplace()
	volft.center_origin_fft()
	volft.fft_shuffle()
	nangle = int(M_PI*r*5) 			# pi*r*cst
	dangle = M_PI/nangle    		# 180* sino

	data = []
	for j in xrange(nangle):
		nuxnew =  cos(dangle*j)
		nuynew = -sin(dangle*j)

		line = volft.extractline(kb,nuxnew,nuynew)

		# filter to omitted u**2
		#line = filt_tanh(line, 0.25, 0.25)
		
		weight = 0

		for k in xrange(0,line.get_xsize()):
			x = line.get_value_at(k)                #*(weight) #(for ccc it was multiplied with weight**2)
			line.set_value_at(k,x)
			weight += k%2
		rlines = fft(line)
		
		data.append(rlines.copy())
	
	e = EMData()
	e.set_size(data[0].get_xsize(),len(data),1)
	for n in xrange(len(data)):
		nx = data[n].get_xsize()
		for i in xrange(nx):
			e.set_value_at(i,n,data[n].get_value_at(i))
	        
	Util.cyclicshift(e, {"dx":M, "dy":0, "dz":0} )

	return Util.window(e,M,len(data),1,0,0,0)


def get_common_line_angles2(phi1,theta1,psi1,phi2,theta2,psi2,nangle, fmod):
	SPIDER = Transform3D.EulerType.SPIDER

	R1  = Transform3D(SPIDER,phi1,theta1,psi1);
	R2  = Transform3D(SPIDER,phi2,theta2,psi2);
	R2T = R2.inverse();
	R2to1 = R1*R2T;

	eulerR2to1 = R2to1.get_rotation(SPIDER);
	phiR2to1   = eulerR2to1["phi"];
	thetaR2to1 = eulerR2to1["theta"];
	psiR2to1   = eulerR2to1["psi"];

	#print phiR2to1,thetaR2to1,psiR2to1
	#alphain1 = ( psiR2to1 +450.0)%360.0 ;# - 180.0 ; # or is it -psi?
	#alphain2 = (-phiR2to1 +450.0)%360.0 ;#- 180.0 ; # or is it  phi?


	alphain1 = fmod(psiR2to1 + 270,  360) 
	alphain2 = fmod(-phiR2to1 + 270, 360)
	#alphamin = min(alphain1,alphain2)

	if alphain1 < 0:
		alpha1 = 180 - alphain1
	else:
		alpha1 = alphain1

	if alphain2 < 0:
		alpha2 = 180 - alphain2
	else:
		alpha2 = alphain2
		
	#if alphamin > 180:
	#	alpha1 = alphain1 - 180.0
	#	alpha2 = alphain2 - 180.0

	n1 = int( nangle * (fmod(alpha1, 180.0) / 180.0) ) 
	n2 = int( nangle * (fmod(alpha2, 180.0) / 180.0) )

	return [alphain1, alphain2, n1, n2]


def cml_discrepancy(Phi, Theta, Psi, Prj):
	from math      import pi, fmod
	from utilities import common_line_in3D
	from sys       import exit
	import time

	# vars
	nprj  = len(Phi)
	nlines = ((nprj - 1) * nprj) / 2

	#--------- compute the angles of the common lines in space
	l_phs = [0.0] * nlines  # angle phi of the common lines
	l_ths = [0.0] * nlines  # angle theta of the common lines
	n     = 0
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			l_phs[n], l_ths[n] = common_line_in3D(Phi[i], Theta[i], Phi[j], Theta[j])
			n += 1

	#---------- compute the weights by Voronoi
	tol = 6

	# search the sames cm lines
	mem_i_same = {}
	ocp_same   = [0] * nlines
	for i in xrange(nlines - 1):
		mem_i_same[i] = None
		v = []
		flag = False
		if ocp_same[i] == 0:
			for j in xrange(i + 1, nlines):
				if ocp_same[j] == 0:
					dist = (l_phs[i] - l_phs[j]) ** 2 + (l_ths[i] - l_ths[j]) ** 2
					if dist < tol:
						v.append(j)
						ocp_same[j] = 1
						flag = True
		if flag: mem_i_same[i] = v

	# create the new vector n_phi n_theta without
	n_phi, n_theta = [], []
	LUT   = []
	index = 0
	for n in xrange(nlines):
		if ocp_same[n] == 0:
			n_phi.append(l_phs[n])
			n_theta.append(l_ths[n])
			LUT.append(n)
			index += 1

	# compute the weights with the new list phi and theta
	n_weights = Util.vrdg(n_phi, n_theta)

	# compute the new weights according the sames cm lines
	weights = [-1] * nlines
	for n in xrange(index): 	weights[LUT[n]] = n_weights[n]
	for n in xrange(nlines - 1):
		if mem_i_same[n] is not None:
			val        = weights[n]
			nval       = val / (len(mem_i_same[n]) + 1)
			weights[n] = nval
			for i in mem_i_same[n]: weights[i] = nval

	#----------- discrepancy

	# define var
	nangle = Prj[0].sino.get_ysize()
	d_psi  = pi / nangle 
	com    = [[] for i in xrange(((nprj - 1) * nprj) / 2)]

	# get the angle of the common line in sinogram 
	count = 0
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			com[count] = get_common_line_angles2(Phi[i], Theta[i], Psi[i], Phi[j], Theta[j], Psi[j], nangle, fmod)
			count += 1

	n = 0
	L, L_tot = 0.0, 0.0

	# compute the discrepancy for all sinograms
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			L      = Prj[i].sino.cm_euc(Prj[j].sino, com[n][2], com[n][3], com[n][0], com[n][1])
			L_tot += (L * weights[n])
			n     += 1

	return (-1) * L_tot

# interface between the simplex function to refine the angles anf the function to compute the discrepancy
def cml_refine_agls(vec_in, data):
	from copy import deepcopy
	# vec_in is composed of [phi_i, theta_i, psi_i]
	# data is composed  [[phi_0, ..., phi_n], [theta_0, ..., theta_n], [psi_0, ..., psi_n], [Prj_0, ..., Prj-n], index]
	
	# prepare the variables
	Phi   = deepcopy(data[0])
	Theta = deepcopy(data[1])
	Psi   = deepcopy(data[2])

	Phi[data[4]]   = vec_in[0]
	Theta[data[4]] = vec_in[1]
	Psi[data[4]]   = vec_in[2]

	# compute the discrepancy
	disc = cml_discrepancy(Phi, Theta, Psi, data[3])
	return disc

def cml_discrepancy_pos(even_agls, Prj, weights, data = None):
	from sys import exit
	# define var if it is not the function spin that call the discrepancy
	if data is None:
		from math import pi, fmod
		nprj   = len(Prj)
		nangle = Prj[0].sino.get_ysize()
		d_psi  = pi / nangle
		com    = [[] for i in xrange(((nprj - 1) * nprj) / 2)]

		# who is active?
		iprj = -1
		for i in xrange(nprj):
			if Prj[i].active is True: iprj = i

		# read angles
		agls = []
		for i in xrange(nprj):
			psi = (Prj[i].pos_psi * d_psi * 180) / pi
			tmp = even_agls[Prj[i].pos_agls]
			if Prj[i].mirror:
				agls.append([fmod(tmp[0]+180, 360), 180 - tmp[1], psi])
			else:
				agls.append([tmp[0], tmp[1], psi])

		# compute the common lines
		count = 0
		for i in xrange(nprj - 1):
			for j in xrange(i + 1, nprj):
				com[count] = get_common_line_angles2(agls[i][0], agls[i][1], agls[i][2], agls[j][0], agls[j][1], agls[j][2], nangle, fmod)
				count += 1

	else:
		# data = [iprj, nprj, nangle, d_psi, fmod, com, com_m]
		iprj, nprj, nangle, d_psi, fmod, com, com_m = data

	n = 0
	L, L_tot = 0.0, 0.0

	# compute the discrepancy for all sinograms
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			L      = Prj[i].sino.cm_euc(Prj[j].sino, com[n][2], com[n][3], com[n][0], com[n][1])
			L_tot += (L * weights[n])
			n     += 1

	# compute the discrepancy for all sinograms with mirror angles
	n = 0
	L_m, L_tot_m = 0.0, 0.0

	# compute the discrepancy for all sinograms with mirror angles
	if iprj != -1:
		for i in xrange(nprj - 1):
			for j in xrange(i + 1, nprj):
				L_m       = Prj[i].sino.cm_euc(Prj[j].sino, com_m[n][2], com_m[n][3], com_m[n][0], com_m[n][1])
				L_tot_m  += (L_m * weights[n])
				n        += 1
	
		# choose the best discrepancy
		if L_tot_m < L_tot:
			Prj[iprj].mirror = True
			disc             = (-1) * L_tot_m
		else:
			Prj[iprj].mirror = False
			disc             = (-1) * L_tot
	else:
		disc = (-1) * L_tot
		
	return Prj, disc

def cml_cmlines_3D(even_agls, Prj):
	from utilities import common_line_in3D
	from sys       import exit

	# vars
	nprj  = len(Prj)
	nline = ((nprj - 1) * nprj) / 2

	# prepare the list of angle
	agls = []
	for i in xrange(nprj):	agls.append(even_agls[Prj[i].pos_agls])
	
	l_phs = [0.0] * nline  # angle phi of the common lines
	l_ths = [0.0] * nline  # angle theta of the common lines
	
	lines = []

	n = 0
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			l_phs[n], l_ths[n] = common_line_in3D(agls[i][0], agls[i][1], agls[j][0], agls[j][1])
			#print 'i', i, 'j', j,'\t%10.3f\t%10.3f' % (l_phs[n], l_ths[n])
			n += 1

	return l_phs, l_ths

def cml_spin(even_agls, Prj, weights):
	from math   import pi, fmod
	from copy   import deepcopy
	from sys    import exit

	# vars
	nprj    = len(Prj)
	npsi    = 2 * Prj[0].sino.get_ysize()
	nlines  = ((nprj - 1) * nprj) / 2
	com     = [[] for i in xrange(nlines)]
	com_m   = [[] for i in xrange(nlines)]
	nangle  = Prj[0].sino.get_ysize()
	d_psi   = pi / nangle

	# who is active?
	iprj = -1
	for i in xrange(nprj):
		if Prj[i].active is True: iprj = i

	# prepare data
	#data = [iprj, nprj, nangle, d_psi, fmod, com, com_m]
	data      = [0] * 6
	data[0:4] = [iprj, nprj, nangle, d_psi, fmod]

	#mem     = []
	pos_max = 0
	bst_pos = 0
	mirror  = False

	# init value of discrepancy
	val_max = -1e10

	# prepare angles
	agls, agls_m = [], []
	for i in xrange(nprj):
		psi = (Prj[i].pos_psi * d_psi * 180) / pi
		tmp = even_agls[Prj[i].pos_agls]

		# if the angle of Prj is a mirror
		if Prj[i].mirror:
			agls.append([fmod(tmp[0]+180, 360), 180 - tmp[1], psi])
		else:
			agls.append([tmp[0], tmp[1], psi])

		# to compute the discrepancy of the mirror angle of the Prj active
		if i == iprj:
			agls_m.append([fmod(tmp[0]+180, 360), 180 - tmp[1], psi])
		else:
			agls_m.append([tmp[0], tmp[1], psi])

	# compute the common line
	agls[iprj][2]   = 0.0
	agls_m[iprj][2] = 0.0

	count = 0
	index = 0
	for i in xrange(nprj - 1):
		for j in xrange(i + 1, nprj):
			com[count]   = get_common_line_angles2(agls[i][0], agls[i][1], agls[i][2], agls[j][0], agls[j][1], agls[j][2], nangle, fmod)
			com_m[count] = get_common_line_angles2(agls_m[i][0], agls_m[i][1], agls_m[i][2], agls_m[j][0], agls_m[j][1], agls_m[j][2], nangle, fmod)
			#print 'i', i, 'j', j, com[count]
			count += 1

	# spin function 0 to 360 (0 to npsi)
	for n in xrange(npsi):
		Prj[iprj].pos_psi = n

		# update common lines
		count = 0
		for i in xrange(nprj - 1):
			for j in xrange(i + 1, nprj):
				if i == iprj:
					# increase the value by step
					com[count][0]   = com[count][0] + (d_psi * 180) / pi                                 # a1 + d_psi in degree
					com[count][2]   = com[count][2] + 1                                                  # n1 + 1
					com_m[count][0] = com_m[count][0] + (d_psi * 180) / pi                               # a1 + d_psi in degree
					com_m[count][2] = com_m[count][2] + 1                                                # n1 + 1
				
					# check value
					if com[count][0] > 360:            com[count][0]   = fmod(com[count][0], 360)        # a1 mod 360
					if com_m[count][0] > 360:          com_m[count][0] = fmod(com_m[count][0], 360)
					if com[count][2] > (nangle - 1):   com[count][2]   = com[count][2] - nangle          # n1 mod nangle
					if com_m[count][2] > (nangle - 1): com_m[count][2] = com_m[count][2] - nangle
				elif j == iprj:
					# increase the value by step
					com[count][1]   = com[count][1] + (d_psi * 180) / pi                                 # a2 + d_psi in degree
					com[count][3]   = com[count][3] + 1			                             # n2 + 1
					com_m[count][1] = com_m[count][1] + (d_psi * 180) / pi                               # a2 + d_psi in degree
					com_m[count][3] = com_m[count][3] + 1
					
					# check value
					if com[count][1] > 360:            com[count][1]   = fmod(com[count][1], 360)        # a2 mod 360
					if com_m[count][1] > 360:          com_m[count][1] = fmod(com_m[count][1], 360)      # a2 mod 360
					if com[count][3] > (nangle - 1):   com[count][3]   = com[count][3] - nangle          # n2 mod nangle
					if com_m[count][3] > (nangle - 1): com_m[count][3] = com_m[count][3] - nangle

				count += 1

		# update data
		data[5] = com
		data[6] = com_m
		Prj, val_new = cml_discrepancy_pos(even_agls, Prj, weights, data)

		# choose the best
		if val_new >= val_max:
			val_max = val_new
			bst_pos = Prj[iprj].pos_psi
			mirror  = Prj[iprj].mirror

	Prj[iprj].pos_psi = bst_pos
	
	Prj[iprj].mirror = mirror
	
	return Prj, val_max

def cml_voronoi(prj_stack, outdir, delta, rand_seed=1000, refine = False, debug = False):
	from random    import random, shuffle, seed, randint, randrange
	from string    import replace
	from utilities import get_im, even_angles, read_txt_col
	from copy      import deepcopy
	from utilities import common_line_in3D, amoeba
	from math      import pi, exp, fmod
	from sys       import exit
	import os
	import time

	from utilities import print_begin_msg, print_end_msg, print_msg
	print_begin_msg('find_struct')

	print_msg('Input stack                 : %s\n'     % prj_stack)
	print_msg('Output directory            : %s\n'     % outdir)
	print_msg('Angle step                  : %-4.1f\n' % delta)	
	print_msg('Random seed                 : %i\n'   % rand_seed)
	if refine:
		print_msg('Refinement                  : True\n\n')
	else:
		print_msg('Refinement                  : False\n\n')

	seed(rand_seed)
	#seed(12)

	if os.path.exists(outdir): os.system( 'rm -rf ' + outdir )
	os.mkdir(outdir)

	# --- TO WORKS
	#debug   = True
	T       = 10000
	search  = 'ALL'
	given   = False
	voronoi = True
	#refine  = True
	pickup  = False
	FILTER  = False

	nprj = EMUtil.get_image_count(prj_stack)

	# TEST
	N = nprj
	
	# ----- define structures data ---------------------------------
	class Projection:
		def __init__ (self, sino, pos_agls, pos_psi, mirror, active):
			self.sino     = sino     # sinogram
			self.pos_agls = pos_agls # orientation angles position in list even_angles
			self.pos_psi  = pos_psi  # position of psi (psi = pos_psi * d_psi)
			self.mirror   = mirror   # the angle have a opposite direction
			self.active   = active   # if the sinogram is actived to search orientation

		def __str__(self):
			txt = 'pos_agls: %d\tpos_psi: %d\tmirror: %s\tactive: %s' % (self.pos_agls, self.pos_psi, self.mirror, self.active)
			return txt

	givPrj, Prj = [], []
	for i in xrange(nprj):
		Prj.append(Projection(None, -1, -1, False, False))
		if given: givPrj.append(Projection(None, -1, -1, False, False))
				
 	# ------ Open and transform images --------------------------------
	#allsinos = [None] * nprj
	givenlst = []

	if pickup:
		## TEST
		# pickup randomly 10 prj in stack_m15
		v = []
		n = 0
		while n < 8:
			if n == 0:
				data  = get_im(prj_stack, 0)
				dic   = data.get_attr_dict()
				if FILTER:
					val = []
					for n in xrange(data.get_xsize()): val.append(float(n))
					from filter import filt_table, filt_tanl
					data = filt_table(data, val)
					data = filt_tanl(data, 0.15, 0.05)
				allsinos[n] = sinogram2( data )
				allsinos[n].set_attr( 'iprj', 0 )
				#### TEST for angle given also
				givenlst.append([dic['phi'], dic['theta'], dic['psi']])
				n    += 1
			else:
				# pick up the ten first
				data = get_im(prj_stack, n)
				dic  = data.get_attr_dict()
				if FILTER:
					val = []
					for n in xrange(data.get_xsize()): val.append(float(n))
					from filter import filt_table, filt_tanl
					data = filt_table(data, val)
					data = filt_tanl(data, 0.15, 0.05)
				allsinos[n] = sinogram2( data )
				allsinos[n].set_attr( 'iprj', 0 )
				#### TEST for angle given also
				givenlst.append([dic['phi'], dic['theta'], dic['psi']])
				n    += 1
				
				
				'''
				i = randrange(1, N-1)
				if i not in v:
					# read angle
					data = get_im(prj_stack, i)
					dic  = data.get_attr_dict()
									
					# compute the distance
					dist = dic['phi'] + dic['theta']

					# if near to zero pickup
					if dist < 150:
						allsinos[n] = sinogram( data )
						allsinos[n].set_attr( 'iprj', i )
				                #### TEST for angle given also
						givenlst.append([dic['phi'], dic['theta'], dic['psi']])
						v.append(i)
						n += 1
				'''
		# add 2 angles randomly
		m = n - 1
		while m < nprj:
			i = randrange(1, N-1)
			if i not in v:
				# read angle
				data = get_im(prj_stack, i)
				dic  = data.get_attr_dict()

				# compute the distance
				dist = dic['phi'] + dic['theta']

				# if near to zero pickup
				if dist > 50:
					
					allsinos[m] = sinogram2( data )
					allsinos[m].set_attr( 'iprj', i )
					#### TEST for angle given also
					givenlst.append([dic['phi'], dic['theta'], dic['psi']])
					v.append(i)
					m += 1
				
	else:

		for i in xrange(nprj):
			data = get_im(prj_stack, i)
			dic  = data.get_attr_dict()
			if FILTER:
				val = []
				for n in xrange(data.get_xsize()): val.append(float(n))
				from filter import filt_table, filt_tanl
				data = filt_table(data, val)
				data = filt_tanl(data, 0.15, 0.05)
				#data.write_image('stackd10_after_filt.hdf', i)
			Prj[i].sino = sinogram2(data)
			#allsinos[i] = sinogram2(data)
			#allsinos[i].set_attr( 'iprj', i )
			#### TEST for angle given also
			if given: givenlst.append([dic['phi'], dic['theta'], dic['psi']])

	if given:
		pagls = []
		for n in xrange(nprj):
			pagls.append([givenlst[n][0], givenlst[n][1], givenlst[n][2]])
		im = plot_angles(pagls)
		#im.write_image('test.spi')

	# some variable
	d_psi  = pi / Prj[0].sino.get_ysize()
	nlines = ((nprj - 1) * nprj) / 2

	# ------Define list of angle randomly distribute------------------
	anglst   = even_angles(delta, 0.0, 89.9, 0.0, 359.9, 'S')

	#### TEST include my given angles
	if given:
		for i in xrange(1, len(anglst)): givenlst.append(anglst[i])
		anglst = deepcopy(givenlst)
	
	n_anglst = len(anglst)
	ocp_agls = [-1] * n_anglst               # list of occupied angles	

	# -------- compute the discreancy for the angles given -----------	
	if given:
		
		# read the given informations
		for n in xrange(nprj):
			#Prj[n].sino     = allsinos[n]
			Prj[n].pos_agls = n
			Prj[n].pos_psi  = int(((anglst[n][2] * pi) / 180) / d_psi)

			ocp_agls[n] = n

		## TEST refine assign one agls from the distributed list
		#ocp_agls[Prj[2].pos_agls] = -1
		#Prj[2].pos_agls = 30
		#anglst[2] = [10, 10, 10]
		#ocp_agls[Prj[2].pos_agls] = 2

		# change all agls
		#for n in xrange(1, nprj):
		#	ocp_agls[Prj[n].pos_agls] = -1
		#	Prj[n].pos_agls = 30 + n
		#	ocp_agls[Prj[n].pos_agls] = n
		
		for n in xrange(nprj): print anglst[Prj[n].pos_agls]

		if voronoi:
			# compute the weight for each common lines with Voronoi
			weights, val1, val2 = cml_weights(anglst, Prj, nlines, True)
		
			# compute the discrepancy
			Prj, disc = cml_discrepancy_pos(anglst, Prj, weights)

			print 'with voronoi:', disc
		else:
			nlines  = ((nprj - 1) * nprj) / 2
			weights = [1] * nlines

			# compute the discrepancy
			Prj, disc = cml_discrepancy_pos(anglst, Prj, weights)

			print disc

			print 'without vornoi:', disc
	
	
        # check if the number of orientation is enough
	if n_anglst < nprj:
		print 'Not enough angles in the list of orientation!'
		exit()

	# ------- init filte to info display ---------------------------
	finfo = outdir + '/progress'
	infofile    = open(finfo, "w")
	infofile.write( 'delta, nangle: %f %d\n' % (delta, len(anglst)) )
	infofile.close()
	angfilepath = outdir + replace( '/angle.txt', ' ', '0' )
	angfile     = open(angfilepath, 'w')
	angfile.close()
	
	# -------- prepare sinograms -----------------------------------
	if not given:
		#prjorders = range(1, nprj)
		#shuffle(prjorders)

		# first sino is the first
		#Prj[0].sino = allsinos[0]
	
		# the other is randomly
		#n = 1
		#for i in prjorders:
		#	Prj[n].sino = allsinos[i].copy()
		#	n += 1
	
		#del allsinos

		# --------- assign the direction of the first sinograms ----------
		Prj[0].pos_agls = 0     # assign (phi=0, theta=0)
		Prj[0].pos_psi  = 0     # assign (psi)
		ocp_agls[0]     = 0     # first position angles is occupied by sino 0

		# -------- assign randomly direction for the others sinograms ----
		# for general case
		n = 1
		while n < nprj:
			i = randint(1, n_anglst - 1)
			if ocp_agls[i] == -1:
				Prj[n].pos_agls    = i
				Prj[n].pos_psi     = randrange(0, Prj[0].sino.get_ysize())
				ocp_agls[i]        = n
				n += 1

	# ---------- loop for all sinograms ---------------------------------
	list_prj = range(1, nprj)
	shuffle(list_prj)
	progress = -1
	for iprj in list_prj:

		progress += 1

		## DEBUG
		if debug: print '>>' + str(iprj)

		# change the active sinogram iprj
		Prj[iprj].active = True

		# ----- loop for all angles from the list even_anglst
		run  = True
		iagl = -1

		## TEST

		#val_time = 0
		g_time = time.time()

		while run:
			s_time = time.time()
			# new angle test
			iagl += 1

			if voronoi:
				# compute the weight for each common lines with Voronoi
				weights, val1, val2 = cml_weights(anglst, Prj, nlines, False)
			else:
				nlines = ((nprj - 1) * nprj) / 2
				weights = [1] * nlines

			# spin for psi of iprj projection			
			Prj, disc = cml_spin(anglst, Prj, weights)

			# if it is the first iteration init old_disc with the first disc
			if iagl == 0:	old_disc = disc

			# informations display
			infofile = open(finfo, 'a')
			txt_i = replace('%2d' % iprj, ' ', '0')
			txt_a = replace('%3d' % iagl, ' ', '0')
			txt   = 'iprj: %s iagl: %s >> Agls (phi, theta): %10.3f %10.3f\t Disc: %10.3f' \
				% (txt_i, txt_a, anglst[Prj[iprj].pos_agls][0], anglst[Prj[iprj].pos_agls][1], abs(disc))
			if Prj[iprj].mirror:
				infofile.write(txt + ' *\n')
			else:
				infofile.write(txt + '\n')
			infofile.close()

			# ---- strategie to new orientationn of the current sinograms ----------------------

			# == search all angles one by one ==
			if search == 'ALL':

				# select the best Prj
				if disc >= old_disc:
					best_Prj = deepcopy(Prj[iprj])
					old_disc = disc

				# choose the next
				old_pos = Prj[iprj].pos_agls
				while ocp_agls[Prj[iprj].pos_agls] != -1:
					Prj[iprj].pos_agls += 1
					if Prj[iprj].pos_agls > (n_anglst - 1):
						Prj[iprj].pos_agls = 1

				# control running
				if iagl > (n_anglst - nprj) - 1:
					run = False

			# == search with simulated annealing ==
			elif search == 'SA':
				# define the probability of new state
				flag = 0
				if exp( -((disc - old_disc)**2) / float(T) ) < random():
					flag = 1
					if disc > old_disc:
						best_Prj = deepcopy(Prj)
						old_disc = disc
						flag = 2

				## DEBUG
				p = exp( -((disc - old_disc)**2) / float(T) )
				print disc, old_disc
				txt = ''
				txt += 'T ' + str(T) + ' p ' + str(p)
				if flag == 0:
					 txt += ' chosse another'
				elif flag == 1:
					 txt += ' choose best (not best)'
				elif flag == 2:
					 txt += ' choose best (the best)'
				print txt

				# choose free angles
				old_pos = Prj[iprj].pos_agls
				while ocp_agls[Prj[iprj].pos_agls] != -1:
					i = randint(1, n_anglst - 1)
					Prj[iprj].pos_agls = i

				# decrease the temperature
				#T *= .99
				T *= .90
				#T -= 1000

				# control running
				if iagl > (n_anglst - nprj) - 1 or T < 1:
					run = False

			# update list of occupied angles
			ocp_agls[old_pos]            = -1
			ocp_agls[Prj[iprj].pos_agls] = iprj

			## DEBUG
			if debug: print 'agl', iagl , 'time:', time.time() - s_time #, 'b sum w:', val1, 'a sum w:', val2

		if debug: print 'Time:', time.time() - g_time

		# ----- assign the best couple angle of sinogram iprj and psis.
		# Update the list of occupied angles
		ocp_agls[Prj[iprj].pos_agls] = -1
		Prj[iprj]                    = deepcopy(best_Prj)
		ocp_agls[Prj[iprj].pos_agls] = iprj

		# change the active sinogram iprj
		Prj[iprj].active = False

		# display informations
		infofile = open(finfo, 'a')
		if Prj[iprj].mirror:
			infofile.write('>> Choose Agls (phi, theta): %10.3f %10.3f mirror Disc: %10.3f\n'
				       % (anglst[Prj[iprj].pos_agls][0], anglst[Prj[iprj].pos_agls][1], abs(old_disc)))
			infofile.write('>> Mirror Agls (phi, theta): %10.3f %10.3f\n\n\n'
				       % ((anglst[Prj[iprj].pos_agls][0] + 180) % 360, 180 - anglst[Prj[iprj].pos_agls][1]))
		else:
			infofile.write('>> Choose Agls (phi, theta): %10.3f %10.3f Disc: %10.3f\n\n\n'
				       % (anglst[Prj[iprj].pos_agls][0], anglst[Prj[iprj].pos_agls][1], abs(old_disc)))
		infofile.close()

		# export the results
		angfile = open(angfilepath, 'a')
		angfile.write('|%d|-----------------------------------------------%s---------\n' % (progress+1, time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime())) )
		for i in xrange(nprj):
			if i == iprj:
				if Prj[i].mirror:
					angfile.write('%10.3f\t%10.3f\t%10.3f <--\n'
					    % ((anglst[Prj[i].pos_agls][0] + 180) % 360, 180 - anglst[Prj[i].pos_agls][1], (Prj[i].pos_psi * d_psi * 180) / pi ))
				else:
					angfile.write('%10.3f\t%10.3f\t%10.3f <--\n'
					    % ( anglst[Prj[i].pos_agls][0],  anglst[Prj[i].pos_agls][1], (Prj[i].pos_psi * d_psi * 180) / pi ))
			else:
				if Prj[i].mirror:
					angfile.write('%10.3f\t%10.3f\t%10.3f\n'
					    % ((anglst[Prj[i].pos_agls][0] + 180) % 360, 180 - anglst[Prj[i].pos_agls][1], (Prj[i].pos_psi * d_psi * 180) / pi ))
				else:
					angfile.write('%10.3f\t%10.3f\t%10.3f\n'
					    % ( anglst[Prj[i].pos_agls][0], anglst[Prj[i].pos_agls][1], (Prj[i].pos_psi * d_psi * 180) / pi ))
		angfile.write('\nDiscrepancy: %10.3f\n\n' % abs(old_disc))
		angfile.close()


	

	# ----- prepare angles to export
	Phi, Theta, Psi = [], [], []
	for n in xrange(nprj):
		if debug: print Prj[n]
		if Prj[n].mirror:
			Phi.append(fmod(anglst[Prj[n].pos_agls][0] + 180, 360.))
			Theta.append(180 - anglst[Prj[n].pos_agls][1])
		else:
			Phi.append(anglst[Prj[n].pos_agls][0])
			Theta.append(anglst[Prj[n].pos_agls][1])
			
		Psi.append((Prj[n].pos_psi * d_psi * 180) / pi)

	# ----- refine angles ---------------------------------
	scales = [delta] * (nprj + 2)

	# if refine use simplexe
	if refine:
		for iprj in xrange(1, nprj):
			# info display
			angfile = open(angfilepath, 'a')
			angfile.write('|%d|-REFINE----------------------------------------%s---------\n' % (iprj, time.strftime('%a_%d_%b_%Y_%H_%M_%S', time.localtime())) )

			# prepare vec_in
			vec_in = []
			vec_in.append(Phi[iprj])            # phi   agls iprj
			vec_in.append(Theta[iprj])          # theta agls iprj
			vec_in.append(Psi[iprj])            # psi   agls iprj
		
			# prepare vec_data
			vec_data = [Phi, Theta, Psi, Prj, iprj]

			# simplex
			optvec, disc, niter = amoeba(vec_in, scales, cml_refine_agls, data=vec_data)
					
			# assign new angles refine
			Phi[iprj]   = optvec[0]
			Theta[iprj] = optvec[1]
			Psi[iprj]   = optvec[2]

			# info display
			for i in xrange(nprj):
				if i == iprj:
					angfile.write('%10.3f\t%10.3f\t%10.3f <--\n'
					    % (Phi[i], Theta[i], Psi[i]))
				else:
					angfile.write('%10.3f\t%10.3f\t%10.3f\n'
					    % (Phi[i], Theta[i], Psi[i]))
			angfile.write('\nDiscrepancy: %10.3f\n\n' % abs(disc))
			angfile.close()
	
	# ----- export the results, each images have attributes (phi, theta, psi)
	pagls = []
	for i in xrange(nprj):
		#id_sino = Prj[i].sino.get_attr('iprj')
		data = get_im(prj_stack, i)
		data.set_attr('phi',   Phi[i])
		data.set_attr('theta', Theta[i])
		data.set_attr('psi',  Psi[i])
		data.set_attr('s2x', 0)
		data.set_attr('s2y', 0)
		data.set_attr('active', 1)
		msg = "Projection #%3d: phi %10.5f theta %10.5f psi %10.5f\n" % (i, Phi[i], Theta[i], Psi[i])
		data.write_image( outdir + "/result.hdf", i )
		print_msg(msg)

		# prepare angles to plot
		pagls.append([Phi[i], Theta[i], Psi[i]])

	print_msg('\nDiscrepancy: %10.3f\n\n' % abs(disc))

	# plot angles
	im = plot_angles(pagls)
	im.write_image(outdir + '/plot_agls.hdf')
	
	print_end_msg("find_struct")

# compute the weight of the common lines
def cml_weights(agls, prj, nlines, flag2):
	from sys import exit

	# var tol
	tol = 6

	# compute the angles of the common lines in space
	phi, theta = cml_cmlines_3D(agls, prj)

	if flag2:
		print 'org:--------------------------------------'
		for n in xrange(nlines): print '%d\t%10.3f\t%10.3f' % (n, phi[n], theta[n])
		print '\n'


	# compute the cst weights if number of lines is less than 22
	#if nlines < 22: weights = [ 6.28 / nlines ] * nlines

	# search the sames cm lines
	mem_i_same = {}
	ocp_same   = [0] * nlines
	for i in xrange(nlines - 1):
		mem_i_same[i] = None
		v = []
		flag = False
		if ocp_same[i] == 0:
			for j in xrange(i + 1, nlines):
				if ocp_same[j] == 0:
					dist = (phi[i] - phi[j]) ** 2 + (theta[i] - theta[j]) ** 2
					if dist < tol:
						v.append(j)
						ocp_same[j] = 1
						flag = True
		if flag: mem_i_same[i] = v

	if flag2:
		print '\n', mem_i_same, '\n'
		print '\n', ocp_same, '\n'

	# create the new vector n_phi n_theta without
	n_phi, n_theta = [], []
	LUT   = []
	index = 0
	for n in xrange(nlines):
		if ocp_same[n] == 0:
			n_phi.append(phi[n])
			n_theta.append(theta[n])
			LUT.append(n)
			index += 1

	if flag2:
		print 'before vor:--------------------------------------'
		for n in xrange(len(n_phi)): print '%d\t%10.3f\t%10.3f' % (n, n_phi[n], n_theta[n])
		print '\n'


	# compute the weights with the new list phi and theta
	n_weights = Util.vrdg(n_phi, n_theta)

	val1 = sum(n_weights)

	# compute the new weights according the sames cm lines
	weights = [-1] * nlines
	for n in xrange(index): 	weights[LUT[n]] = n_weights[n]
	for n in xrange(nlines - 1):
		if mem_i_same[n] is not None:
			val        = weights[n]
			nval       = val / (len(mem_i_same[n]) + 1)
			weights[n] = nval
			for i in mem_i_same[n]: weights[i] = nval

	if flag2:
		print 'after:--------------------------------------'
		for n in xrange(nlines): print '%d\t%10.3f\t%10.3f\t%f' % (n, phi[n], theta[n], weights[n])
		print '\n'

	
	val2 = sum(weights)
	

	# return the weights
	return weights, val1, val2



## END COMMON LINES OLD VERSION ###############################################################
###############################################################################################


###############################################################################################
## COMMON LINES NEW VERSION ###################################################################
## 10/03/2008

# to utilities: get_line
def get_line(im, li):
	from utilities import model_blank
	nx = im.get_xsize()
	e  = model_blank(nx)
	for n in xrange(nx): e.set_value_at(n, 0, im.get_value_at(n, li))
	return e

# transform an image to sinogram (mirror include)
def cml_sinogram_dev(image2D, diameter, d_psi):
	from math         import cos, sin
	from fundamentals import fft
	
	M_PI  = 3.141592653589793238462643383279502884197
	
	# prepare 
	M = image2D.get_xsize()
	# padd two times
	npad  = 2
	N     = M * npad
	# support of the window
	K     = 6
	alpha = 1.75
	r     = M / 2
	v     = K / 2.0 / N

	kb     = Util.KaiserBessel(alpha, K, r, K / (2. * N), N)
	volft  = image2D.average_circ_sub()  	# ASTA - in spider
	volft.divkbsinh(kb)		  	# DIVKB2 - in spider
	volft  = volft.norm_pad(False, npad)
	volft.do_fft_inplace()
	volft.center_origin_fft()
	volft.fft_shuffle()

	# get line projection
	nangle = int(360 / d_psi)     
	dangle = 2 * M_PI / float(nangle)
	data   = []
	for j in xrange(nangle):
		nuxnew =  cos(dangle * j)
		nuynew = -sin(dangle * j)
		line   = volft.extractline(kb, nuxnew, nuynew)
		rlines = fft(line)
		data.append(rlines.copy())

	# copy each line in the same im
	e = EMData()
	e.set_size(data[0].get_xsize() ,len(data), 1)
	for n in xrange(len(data)):
		nx = data[n].get_xsize()
		for i in xrange(nx): e.set_value_at(i, n, data[n].get_value_at(i))

	Util.cyclicshift(e, {"dx":M, "dy":0, "dz":0} )

	return Util.window(e, diameter, len(data), 1, 0, 0, 0)

def common_line_in3D_dev(ph1, th1, ph2, th2):
	from math import pi, sqrt, cos, sin, asin, acos

	deg_rad = pi / 180.0
	ph1 *= deg_rad 
	th1 *= deg_rad 
	ph2 *= deg_rad 
	th2 *= deg_rad

	# cross-product between normal vector of projections
	nx = sin(th1)*sin(ph1)*cos(th2) - cos(th1)*sin(th2)*sin(ph2)
	ny = cos(th1)*sin(th2)*cos(ph2) - cos(th2)*sin(th1)*cos(ph1)
	nz = sin(th1)*cos(ph1)*sin(th2)*sin(ph2) - sin(th1)*sin(ph1)*sin(th2)*cos(ph2)

	# normalize
	norm    = nx**2 + ny**2 + nz**2
	rt_norm = sqrt(norm)
	nx /= rt_norm
	ny /= rt_norm
	nz /= rt_norm

	# if theta > 90, apply mirror 
	if nz < 0: nx = -nx; ny = -ny; nz = -nz
	
	# calculate phi and theta (deg)
	thetaCom  = acos(nz)

	if    thetaCom == 0: phiCom = 0
	else:
		val = ny / sin(thetaCom)
		if val > 1.0:  val = 1.0
		if val < -1.0: val = -1.0
		phiCom = asin(val)
	
		phiCom    = (phiCom * 180 / pi + 360)%360
		thetaCom *= (180 / pi)

	return phiCom , thetaCom

def cml_weights_full_dev(Ori):
	from development   import common_line_in3D_dev

	# gbl vars
	global g_n_prj, g_n_lines, g_anglst

	
	# gbl vars
	l_phs  = [0.0] * g_n_lines  # angle phi of the common lines
	l_ths  = [0.0] * g_n_lines  # angle theta of the common lines
	n      = 0
	for i in xrange(g_n_prj - 1):
		for j in xrange(i + 1, g_n_prj):
			l_phs[n], l_ths[n] = common_line_in3D_dev(Ori[4*i], Ori[4*i+1], Ori[4*j], Ori[4*j+1])
			n+= 1

	tol = 3

	# search the closer cml lines
	ocp_same   = [-1] * g_n_lines
	num_agl    = 0
	for i in xrange(g_n_lines):
	    if ocp_same[i] == -1:
		ocp_same[i] = num_agl
		for j in xrange(i + 1, g_n_lines):
		    if ocp_same[j] == -1:
			dist = (l_phs[i] - l_phs[j])**2 + (l_ths[i] - l_ths[j])**2
			if dist < tol: ocp_same[j] = num_agl

		num_agl += 1

	if num_agl > 2:

		# create the new vector n_phi n_theta without closer
		n_phi   = [0.0] * num_agl
		n_theta = [0.0] * num_agl
		nb_same = [0]   * num_agl
		num_agl = 0
		for n in xrange(g_n_lines):
		    nb_same[ocp_same[n]] += 1
		    if ocp_same[n] == num_agl:
			n_phi[num_agl]   = l_phs[n]
			n_theta[num_agl] = l_ths[n]
			num_agl += 1

		# Voronoi
		n_weights = Util.vrdg(n_phi, n_theta)

		weights = [0.0] * g_n_lines
		for i in xrange(g_n_lines):
			if nb_same[ocp_same[i]] > 1:
				weights[i] = n_weights[ocp_same[i]] / float(nb_same[ocp_same[i]])
			else:
				weights[i] = n_weights[ocp_same[i]]

	else:
		weights = [6.28/float(g_n_lines)] * g_n_lines

	return weights
	

# compute the weight of the common lines
def cml_weights_iagl_dev(Ori, iagl, iprj):
	from development   import common_line_in3D_dev

	# gbl vars
	global g_n_prj, g_n_lines, g_anglst

	
	# gbl vars
	l_phs  = [0.0] * g_n_lines  # angle phi of the common lines
	l_ths  = [0.0] * g_n_lines  # angle theta of the common lines
	n      = 0
	for i in xrange(g_n_prj - 1):
		for j in xrange(i + 1, g_n_prj):
			if i == iprj:   l_phs[n], l_ths[n] = common_line_in3D_dev(g_anglst[iagl][0], g_anglst[iagl][1], Ori[4*j], Ori[4*j+1])
			elif j == iprj:	l_phs[n], l_ths[n] = common_line_in3D_dev(Ori[4*i], Ori[4*i+1], g_anglst[iagl][0], g_anglst[iagl][1])
			else:		l_phs[n], l_ths[n] = common_line_in3D_dev(Ori[4*i], Ori[4*i+1], Ori[4*j], Ori[4*j+1])
			n+= 1

	tol = 3

	# search the closer cml lines
	ocp_same   = [-1] * g_n_lines
	num_agl    = 0
	for i in xrange(g_n_lines):
	    if ocp_same[i] == -1:
		ocp_same[i] = num_agl
		for j in xrange(i + 1, g_n_lines):
		    if ocp_same[j] == -1:
			dist = (l_phs[i] - l_phs[j])**2 + (l_ths[i] - l_ths[j])**2
			#print i, j, dist
			if dist < tol: ocp_same[j] = num_agl

		num_agl += 1

	if num_agl > 2:

		# create the new vector n_phi n_theta without closer
		n_phi   = [0.0] * num_agl
		n_theta = [0.0] * num_agl
		nb_same = [0]   * num_agl
		num_agl = 0
		for n in xrange(g_n_lines):
		    nb_same[ocp_same[n]] += 1
		    if ocp_same[n] == num_agl:
			n_phi[num_agl]   = l_phs[n]
			n_theta[num_agl] = l_ths[n]
			num_agl += 1

		# Voronoi
		n_weights = Util.vrdg(n_phi, n_theta)

		weights = [0.0] * g_n_lines
		for i in xrange(g_n_lines):
			if nb_same[ocp_same[i]] > 1:
				weights[i] = n_weights[ocp_same[i]] / float(nb_same[ocp_same[i]])
			else:
				weights[i] = n_weights[ocp_same[i]]

	else:
		weights = [6.28/float(g_n_lines)] * g_n_lines

	return weights

# compute the weight of the common lines
def cml_weights_iagl_old(Ori, iagl, iprj):
	from development   import common_line_in3D_dev

	# gbl vars
	global g_n_prj, g_n_lines, g_anglst

	
	# gbl vars
	l_phs  = [0.0] * g_n_lines  # angle phi of the common lines
	l_ths  = [0.0] * g_n_lines  # angle theta of the common lines
	n      = 0
	for i in xrange(g_n_prj - 1):
		for j in xrange(i + 1, g_n_prj):
			if i == iprj:   l_phs[n], l_ths[n] = common_line_in3D_dev(g_anglst[iagl][0], g_anglst[iagl][1], Ori[4*j], Ori[4*j+1])
			elif j == iprj:	l_phs[n], l_ths[n] = common_line_in3D_dev(Ori[4*i], Ori[4*i+1], g_anglst[iagl][0], g_anglst[iagl][1])
			else:		l_phs[n], l_ths[n] = common_line_in3D_dev(Ori[4*i], Ori[4*i+1], Ori[4*j], Ori[4*j+1])
			n += 1

	
	# Voronoi
	weights = Util.vrdg(l_phs, l_ths)

	if iagl == 729 and iprj == 18:
		for n in xrange(len(l_phs)):
			print '%6.3f %6.3f' % (l_phs[n], l_ths[n])

		print '\n\n', weights


	return weights

def cml_weights_full_old(Ori):
	from development   import common_line_in3D_dev

	# gbl vars
	global g_n_prj, g_n_lines, g_anglst
	
	# gbl vars
	l_phs  = [0.0] * g_n_lines  # angle phi of the common lines
	l_ths  = [0.0] * g_n_lines  # angle theta of the common lines
	n      = 0
	for i in xrange(g_n_prj - 1):
		for j in xrange(i + 1, g_n_prj):
			l_phs[n], l_ths[n] = common_line_in3D_dev(Ori[4*i], Ori[4*i+1], Ori[4*j], Ori[4*j+1])
			n+= 1

	# Voronoi
	weights = Util.vrdg(l_phs, l_ths)

	return weights



		
'''
#####
# OLD CODE WEIGHTS COMPLETE
####

#####
# OLD CODE WEIGHTS
####

tol = 0.5

# search the sames cm lines
mem_i_same = [[] for i in xrange(g_n_lines)]
ocp_same   = [0] * g_n_lines
for i in xrange(g_n_lines - 1):
	mem_i_same[i] = None
	v = []
	flag = False
	if ocp_same[i] == 0:
		for j in xrange(i + 1, g_n_lines):
			if ocp_same[j] == 0:
				dist = (l_phs[i] - l_phs[j])**2 + (l_ths[i] - l_ths[j])**2
				if dist < tol:
					v.append(j)
					ocp_same[j] = 1
					flag = True
	if flag: mem_i_same[i] = v

if iagl:
	t1 = time.time()
	print 'Old merging', t1-t, 's'

# create the new vector n_phi n_theta without closer
n_phi, n_theta = [], []
LUT   = []
index = 0
for n in xrange(g_n_lines):
	if ocp_same[n] == 0:
		n_phi.append(l_phs[n])
		n_theta.append(l_ths[n])
		LUT.append(n)
		index += 1

if iagl:
	t2 = time.time()
	print 'Old new v', t2-t1, 's'

# use Voronoi
n_weights = Util.vrdg(n_phi, n_theta)

if iagl:
	t3 = time.time()
	print 'Old vor', t3-t2, 's'

# compute the new weights according the sames cm lines
weights = [-1] * g_n_lines
for n in xrange(index): weights[LUT[n]] = n_weights[n]
for n in xrange(g_n_lines - 1):
	if mem_i_same[n] is not None:
		val        = weights[n]
		nval       = val / (len(mem_i_same[n]) + 1)
		weights[n] = nval
		for i in mem_i_same[n]: weights[i] = nval

if iagl:
	t4 = time.time()
	print 'Old splitting', t4-t3, 's'



########################################################
if iagl:
	t4 = time.time()
	print 'Cml', t4-t, 's'

'''




# open and transform projections
def cml_open_proj_dev(stack, ir, ou, d_psi, lf, hf):
	#from projection   import cml_sinogram
	from development  import cml_sinogram_dev
	from utilities    import model_circle, get_params_proj, model_blank
	from fundamentals import fft

	nprj = EMUtil.get_image_count(stack)                # number of projections
	Prj = []                                            # list of projections
	Ori = [-1] * 4 * nprj                              # orientation intiale (phi, theta, psi, index) for each projection

	image = EMData()
	for i in xrange(nprj):
		image.read_image(stack, i)

		# read initiale angles if given
		try:	Ori[4*i], Ori[4*i+1], Ori[4*i+2], s2x, s2y = get_params_proj(image)
		except:	pass
		
		if(i == 0):
			nx = image.get_xsize()
			if(ou < 1):
				ou = nx // 2 - 1
			else:
				ou = int(ou) // 2
				ou = 2 * ou +1
			diameter = 2 * ou + 1
			mask2D   = model_circle(ou, nx, nx)
			circ     = mask2D.copy()
			if ou > 1:  circ   -= model_circle(ou - 1, nx, nx)
			if ir > 0:  mask2D -= model_circle(ir, nx, nx)

		# normalize under the mask
		[mean_a, sigma, imin, imax] = Util.infomask(image, circ, True)
		image -= mean_a
		Util.mul_img(image, mask2D)

		# sinogram
		sino = cml_sinogram_dev(image, diameter, d_psi)

		# prepare the cut positions in order to filter (lf: low freq; hf: high freq)
		ihf = min(int(2 * hf * diameter), diameter + (diameter + 1) % 2)
		ihf = ihf + (ihf + 1) % 2    # index ihf must be odd to take the img part
		ilf = max(int(2 * lf * diameter), 0)
		ilf = ilf + ilf % 2          # index ilf must be even to fall in the real part
		bdf = ihf - ilf + 1

		# process lines
		nxe = sino.get_xsize()
		nye = sino.get_ysize()
		prj = model_blank(bdf, nye)
		prj.set_complex(True)
		for li in xrange(nye):

			# get the line li
			line = model_blank(nxe)
			for ci in xrange(nxe): line.set_value_at(ci, 0, sino.get_value_at(ci, li))

			# normalize this line
			[mean_l, sigma_l, imin, imax] = Util.infomask(line, None, True)
			line = (line - mean_l) / sigma_l

			# fft
			line = fft(line)

			# filter (cut part of coef)
			ct = 0
			for ci in xrange(ilf, ihf + 1):
				prj.set_value_at(ct, li, line.get_value_at(ci, 0))
				ct += 1
		
		# store the projection
		Prj.append(prj)

	return Prj, Ori

# export result obtain by the function find_struct
def cml_export_struc_dev(stack, outdir, Ori):
	from projection import plot_angles
	from utilities  import set_params_proj

	global g_n_prj
	
	pagls = []
	data  = EMData()
	for i in xrange(g_n_prj):
		data.read_image(stack, i)
		p = [Ori[4*i], Ori[4*i+1], Ori[4*i+2], 0.0, 0.0]
		set_params_proj(data, p)
		data.set_attr('active', 1)
		data.write_image(outdir + '/structure.hdf', i)

		# prepare angles to plot
		pagls.append([Ori[4*i], Ori[4*i+1], Ori[4*i+2]])

	# plot angles
	im = plot_angles(pagls)
	im.write_image(outdir + '/plot_agls.hdf')

# init the global average used for lot of function to cml
def cml_init_global_var(dpsi, delta, nprj, debug):
	from utilities import even_angles
	global g_anglst, g_d_psi, g_n_psi, g_i_prj, g_n_lines, g_n_prj, g_n_anglst, g_debug
	
	g_anglst   = even_angles(delta, 0.0, 179.9, 0.0, 359.9, 'P')
	g_n_anglst = len(g_anglst)
	g_d_psi    = dpsi
	g_n_psi    = int(360 / dpsi)
	g_i_prj    = -1
	g_n_lines  = ((nprj - 1) * nprj) / 2
	g_n_prj    = nprj
	g_debug    = debug
	

# write the head of the logfile
def cml_head_log_dev(stack, outdir, delta, ir, ou, lf, hf, rand_seed, maxit, given):
	from utilities import print_msg

	# call global var
	global g_anglst, g_n_prj, g_d_psi, g_n_anglst
	
	print_msg('Input stack                  : %s\n'     % stack)
	print_msg('Number of projections        : %d\n'     % g_n_prj)
	print_msg('Output directory             : %s\n'     % outdir)
	print_msg('Angular step                 : %5.2f\n'  % delta)
	print_msg('Sinogram angle accuracy      : %5.2f\n'  % g_d_psi)
	print_msg('Inner particle radius        : %5.2f\n'  % ir)	
	print_msg('Outer particle radius        : %5.2f\n'  % ou)
	print_msg('Filter, minimum frequency    : %5.3f\n'  % lf)
	print_msg('Filter, maximum frequency    : %5.3f\n'  % hf)
	print_msg('Random seed                  : %i\n'     % rand_seed)
	print_msg('Number of maximum iterations : %d\n'     % maxit)
	print_msg('Start from given orientations: %s\n'     % given)
	
	
	#print_msg('Number of trials            : %d\n'     % trials)
	#print_msg('Number of cpus              : %i\n'     % ncpu)
	#if refine:
	#	print_msg('Refinement                  : True\n')
	#else:
	#	print_msg('Refinement                  : False\n')
	print_msg('Number of angles             : %i\n\n'   % g_n_anglst)

# write the end of the logfile
def cml_end_log_dev(Ori, disc, disc_nw, ite):
	from utilities import print_msg
	global g_n_prj
	print_msg('\n\n')
	for i in xrange(g_n_prj): print_msg('Projection #%s: phi %10.5f    theta %10.5f    psi %10.5f\n' % (str(i).rjust(3, '0'), Ori[4*i], Ori[4*i+1], Ori[4*i+2]))
	print_msg('\nNumber of iterations: %d\n' % ite)
	print_msg('Discrepancy: %10.3f\n' % abs(disc))
	print_msg('Discrepancy without weigths: %10.3f\n' % abs(disc_nw))

# display the list of angles for each iterations
def cml_export_txtagls_dev(outdir, Ori, disc, title):
	import time
	global g_n_prj, g_i_prj

	angfile = open(outdir + '/angles', 'a')

	angfile.write('|%s|-----------------------------------------------%s---------\n' % (title, time.ctime()))
	for i in xrange(g_n_prj): angfile.write('%10.3f\t%10.3f\t%10.3f\n' % (Ori[4*i], Ori[4*i+1], Ori[4*i+2]))
			
	angfile.write('\nDiscrepancy: %10.3f\n\n' % disc)
	angfile.close()

# export the progress of the find_struc function
def cml_export_progress_dev(outdir, ite, iprj, iagl, psi, disc, cmd):
	infofile = open(outdir + '/progress', 'a')
	global g_anglst

	if cmd == 'progress':
		txt_ite = str(ite).rjust(3, '0')
		txt_i   = str(iprj).rjust(3, '0')
		txt_a   = str(iagl).rjust(3, '0')
		txt     = 'Ite: %s Prj: %s Agls: %s >> Agls (phi, theta, psi): %10.3f %10.3f %10.3f   Disc: %10.7f' % (txt_ite, txt_i, txt_a, g_anglst[iagl][0], g_anglst[iagl][1], psi, disc)
		

	elif cmd == 'choose':
		txt   = 'Ite: %s  Select Agls: %s >> Agls (phi, theta, psi): %10.3f %10.3f %10.3f   Disc: %10.7f\n' % (str(ite).rjust(3, '0'), str(iagl).rjust(3, '0'), g_anglst[iagl][0], g_anglst[iagl][1], psi, disc)

	infofile.write(txt + '\n')
	infofile.close()

# compute the common lines in sino
def get_common_line_angles_dev(phi1, theta1, psi1, phi2, theta2, psi2, nangle, STOP=False):
	from math import fmod
	R1    = Transform({"type":"spider", "phi":phi1, "theta":theta1, "psi":psi1})
	R2    = Transform({"type":"spider", "phi":phi2, "theta":theta2, "psi":psi2})
	R2T   = R2.inverse()
	R2to1 = R1*R2T

	eulerR2to1 = R2to1.get_rotation("spider")
	phiR2to1   = eulerR2to1["phi"]
	thetaR2to1 = eulerR2to1["theta"]
	psiR2to1   = eulerR2to1["psi"]

	alphain1 = fmod(psiR2to1  + 270.0, 360.0)
	alphain2 = fmod(-phiR2to1 + 270.0, 360.0)

	n1 = int(nangle * fmod(alphain1 + 360, 360) / 360.0)
	n2 = int(nangle * fmod(alphain2 + 360, 360) / 360.0)
	
	return n1, n2

# compute discrepancy according the projections and orientations
def cml_disc_dev(Prj, Ori, flag_weights):
	from development import get_common_line_angles_dev, cml_weights_full_dev
	from math        import pi, fmod

	# gbl vars
	global g_n_prj, g_n_psi, g_n_lines

	if flag_weights:
		cml = Util.cml_line_in3d_full(Ori)    # c-code
		weights = Util.cml_weights(cml)       # c-code
		#weights = cml_weights_full_dev(Ori)  # py-code
		#weights = cml_weights_full_old(Ori)
		
	else:   weights = [1.0] * g_n_lines

	#com = [[] for i in xrange(g_n_lines)]
	com = [0] * 2 * g_n_lines

	# compute the common lines
	count = 0
	for i in xrange(g_n_prj - 1):
		for j in xrange(i + 1, g_n_prj):
			#com[count], com[count + 1] = get_common_line_angles_dev(Ori[4*i], Ori[4*i+1], Ori[4*i+2], Ori[4*j], Ori[4*j+1], Ori[4*j+2], g_n_psi)
			[com[count], com[count + 1]] = Util.cml_line_pos(Ori[4*i], Ori[4*i+1], Ori[4*i+2], Ori[4*j], Ori[4*j+1], Ori[4*j+2], g_n_psi)        # c-code
			count += 2

	n = 0
	L_tot = 0.0

	# compute the discrepancy for all sinograms
	for i in xrange(g_n_prj - 1):
		for j in xrange(i + 1, g_n_prj):
			L      = Prj[i].cm_euc(Prj[j], com[n], com[n + 1])
			L_tot += (L * weights[int(n/2)])
			n     += 2

	return L_tot

# interface between the simplex function to refine the angles and the function to compute the discrepancy
def cml_refine_agls_wrap_dev(vec_in, data):
	# vec_in: [phi_i, theta_i, psi_i]
	# data:   [Prj, Ori, iprj]

	# unpack
	phi, theta, psi = vec_in
	Prj, Ori, iprj  = data

	# prepare the variables
	Ori[4*iprj]   = phi
	Ori[4*iprj+1] = theta
	Ori[4*iprj+2] = psi

	# compute the discrepancy
	disc = cml_disc_dev(Prj, Ori, True)

	return -disc

# cml refines angles
def cml_refine_agls_dev(Prj, Ori, delta):
	from copy      import deepcopy
	from utilities import amoeba
	global g_n_prj
	
	scales = [delta] * (g_n_prj + 2)

	for iprj in xrange(g_n_prj):
		# init vec_in
		vec_in   = [Ori[4*iprj], Ori[4*iprj+1], Ori[4*iprj+2]]

		# prepare vec_data
		vec_data = [Prj, deepcopy(Ori), iprj]

		# simplex
		optvec, disc, niter = amoeba(vec_in, scales, cml_refine_agls_wrap_dev, data = vec_data)

		# assign new angles refine
		Ori[4*iprj]   = (optvec[0]+360)%360
		Ori[4*iprj+1] = optvec[1]
		Ori[4*iprj+2] = optvec[2]

		print 'refine:', iprj, 'angles:', Ori[4*iprj:4*iprj+4], 'disc:', -disc

	return Ori

# cml spin function for one orientation
def cml_spin_dev(Prj, iprj, Ori, iagl, weights):
	#from development import cml_weights_dev, get_common_line_angles_dev
	from math        import pi, fmod
	import sys

	# gbl vars
	global g_n_prj, g_n_psi, g_n_lines, g_anglst
	com = [0] * 2 * g_n_lines

	# compute the common line (only for iprj)
	com = Util.cml_list_line_pos(Ori, g_anglst[iagl][0], g_anglst[iagl][1], iprj, g_n_prj, g_n_psi, g_n_lines)

	# do spin over all psi
	res = Util.cml_spin(g_n_psi, iprj, g_n_prj, weights, com, Prj)

	#return best_disc, best_psi
	return res[0], int(res[1])



# find structure
def cml_find_structure_dev(Prj, Ori, outdir, maxit, first_zero, flag_weights):
	from development import cml_spin_dev, cml_export_progress_dev, cml_weights_iagl_dev
	import time
	import signal
	import sys

	# watchdog to Util.vrdg (voronoi c-code)
	def alarmHandler(signum, frame):
		#raise TimeExceededError, "Voronoi ran too long"
		raise Exception
	
	# global vars
	global g_i_prj, g_n_prj, g_n_anglst, g_anglst, g_d_psi, g_debug, g_n_lines

	# list of free orientation
	ocp = [-1] * g_n_anglst

	if first_zero:
		listprj = range(1, g_n_prj)
		ocp[0]  = 0 
	else:   listprj = range(g_n_prj)
	#listprj = [0, 1]

	# iteration loop
	for ite in xrange(maxit):
		t_start = time.time()

		# loop over i prj
		change = False
		for iprj in listprj:

			# Store current index of angles assign
			cur_agl      = Ori[4*iprj+3]
			ocp[cur_agl] = -1

			# loop over all angles
			best_disc = 1e20
			best_psi  = -1
			best_iagl = -1
			for iagl in xrange(g_n_anglst):

				# if agls free
				if ocp[iagl] == -1:
					# weights
					if flag_weights:
						cml = Util.cml_line_in3d_iagl(Ori, g_anglst[iagl][0], g_anglst[iagl][1], iprj)    # c-code
						signal.signal(signal.SIGALRM, alarmHandler)
						signal.alarm(10)
						try:						
							weights = Util.cml_weights(cml)                        # c-code
						except Exception:
							#print "Voronoi function ran too long!"
							signal.alarm(0)
							sys.exit()
							
						signal.alarm(0)
											
						#weights = cml_weights_iagl_dev(Ori, iagl, iprj)               # py-code
						#weights = cml_weights_iagl_old(Ori, iagl, iprj)
						
					else:   weights = [1.0] * g_n_lines
					
					# spin
					disc, ind_psi = cml_spin_dev(Prj, iprj, Ori, iagl, weights)


					# select the best
					if disc < best_disc:
						best_disc = disc
						best_psi  = ind_psi
						best_iagl = iagl

					if g_debug: cml_export_progress_dev(outdir, ite, iprj, iagl, ind_psi * g_d_psi, disc, 'progress')
				else:
					if g_debug: cml_export_progress_dev(outdir, ite, iprj, iagl, -1, -1, 'progress')

			# if change, assign
			if best_iagl != cur_agl:
				ocp[best_iagl] = iprj
				Ori[4*iprj]    = g_anglst[best_iagl][0] # phi
				Ori[4*iprj+1]  = g_anglst[best_iagl][1] # theta
				Ori[4*iprj+2]  = best_psi * g_d_psi     # psi
				Ori[4*iprj+3]  = best_iagl              # index

				change = True
			else:
				ocp[cur_agl]   = iprj

			if g_debug: cml_export_progress_dev(outdir, ite, iprj, best_iagl, best_psi * g_d_psi, best_disc, 'choose')


		# if one change, compute new full disc
		disc = cml_disc_dev(Prj, Ori, flag_weights)

		if g_debug:
			disc2 = cml_disc_dev(Prj, Ori, False)
			print 'Ite: ', disc, '           %6.2f s     ' % (time.time() - t_start), disc2

		# display in the progress file
		cml_export_txtagls_dev(outdir, Ori, disc, 'Ite: %s' % str(ite + 1).rjust(3, '0'))

		if not change: break

	return Ori, disc, ite
	
# application find structure
def find_struct_dev(stack, outdir, ir, ou, delta, dpsi, lf, hf, rand_seed, maxit, given = False, first_zero = False, flag_weights = False, debug = False):
	from utilities import print_begin_msg, print_msg, print_end_msg, start_time, running_time
	import time
	import os
	import sys

	# logfile
	t_start = start_time()
	print_begin_msg('find_struct')

	if os.path.exists(outdir): os.system('rm -rf ' + outdir)
	os.mkdir(outdir)

	# import
	from development import cml_open_proj_dev, cml_init_global_var, cml_head_log_dev
	from development import cml_disc_dev, cml_export_txtagls_dev, cml_export_struc_dev
	from development import cml_end_log_dev
	from random      import seed, random

	# Open and transform projections
	Prj, Ori = cml_open_proj_dev(stack, ir, ou, dpsi, lf, hf)

	# if not angles given select randomly orientation for each projection
	if not given:
		if rand_seed > 0: seed(rand_seed)
		else:             seed()
		j = 0
		for n in xrange(len(Prj)):
			if first_zero and n == 0:
				Ori[j]   = 0.0
				Ori[j+1] = 0.0
				Ori[j+2] = 0.0
			else:
				Ori[j]   = random() * 360  # phi
				Ori[j+1] = random() * 180  # theta
				Ori[j+2] = random() * 360  # psi
			j += 4

	# Init the global vars
	cml_init_global_var(dpsi, delta, len(Prj), debug)
	
	# Update logfile
	cml_head_log_dev(stack, outdir, delta, ir, ou, lf, hf, rand_seed, maxit, given)

	# Compute the first disc
	disc = cml_disc_dev(Prj, Ori, flag_weights)

	# Update progress file
	cml_export_txtagls_dev(outdir, Ori, disc, 'Init')

	# Find structure
	try:
		Ori, disc, ite = cml_find_structure_dev(Prj, Ori, outdir, maxit, first_zero, flag_weights)
	except SystemExit:
		sys.exit()

	# Export structure
	cml_export_struc_dev(stack, outdir, Ori)

	# Compute disc without weights
	disc_now = cml_disc_dev(Prj, Ori, False)

	# Update logfile
	cml_end_log_dev(Ori, disc, disc_now, ite)
	running_time(t_start)
	print_end_msg('find_struct')

	return 1

# cml init for MPI version
def cml_init_MPI_dev(trials):
	from mpi 	  import mpi_init, mpi_comm_size, mpi_comm_rank, mpi_barrier, MPI_COMM_WORLD
	from utilities    import bcast_number_to_all
	from random       import randint
	import sys
	
	# init
	sys.argv       = mpi_init(len(sys.argv),sys.argv)
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid           = mpi_comm_rank(MPI_COMM_WORLD)

	# chose a random node as a main one
	main_node = 0
	if myid  == 0:	main_node = randint(0, number_of_proc - 1)
	main_node = bcast_number_to_all(main_node, 0)
	mpi_barrier(MPI_COMM_WORLD)

	# define the number of loop per node
	loop = trials / number_of_proc
	if trials % number_of_proc != 0: loop += 1

	return main_node, myid, number_of_proc, loop

# cml init list of rand_seed for trials version
def cml_init_rnd_dev(trials, rand_seed):
	from random import seed, randrange

	if trials == 1: return [rand_seed]
	
	if rand_seed > 0: seed(rand_seed)
	else:             seed()

	r_min = 100
	r_max = 1000000
	f_min = 1
	f_max = 100

	rnd     = []
	itrials = 0
	while itrials < trials:
		val_rnd = randrange(r_min, r_max)
		val_f   = randrange(f_min, f_max)
		val_o   = randrange(0, 2)
		if val_o: val_rnd = int(val_rnd * val_f)
		else:     val_rnd = int(val_rnd / float(val_f))
		if val_rnd not in rnd:
			rnd.append(val_rnd)
			itrials += 1

	return rnd

def find_structure_MPI(stack, trials, ir, ou, delta, dpsi, lf, hf, rand_seed, maxit):
	from development import find_struct_dev, cml_init_rnd_dev, cml_init_MPI_dev
	from mpi         import mpi_barrier, mpi_reduce, mpi_bcast
	from mpi         import MPI_COMM_WORLD, MPI_FLOAT, MPI_INT, MPI_SUM
	import os

	main_node, myid, ncpu, loop = cml_init_MPI_dev(trials)
	Rnd = cml_init_rnd_dev(loop * ncpu, rand_seed)
	print Rnd

	for i in xrange(loop):
		outdir = 'trials_%s' % str(myid * loop + i).rjust(4, '0')
		ret = 0
		try:
			ret = find_struct_dev(stack, outdir, ir, ou, delta, dpsi, lf, hf, Rnd[myid * loop + i], maxit, False, False, True, False)
		except SystemExit:
			ret = 0

		f = open('report_node%s' % str(myid).rjust(2, '0'), 'a')
		if ret: txt = 'passed'
		else:   txt = 'failed'
		f.write('node %s   trials %s: %s\n' % (str(myid).rjust(2, '0'), str(myid * loop + i).rjust(4, '0'), txt))
		f.close()




#-------------------- OLD --------------------------------------------------------------------





## END GA CLUSTERING ##########################################################################
###############################################################################################


"""

def ali3d_dB(stack, ref_vol, outdir, maskfile = None, ir = 1, ou = -1, rs = 1, 
            xr = "4 2 2 1", yr = "-1", ts = "1 1 0.5 0.25", delta = "10 6 4 4", an="-1",
	    center = 1, maxit = 5, CTF = False, snr = 1.0,  ref_a="S", sym="c1"):
	#  THIS IS FOR PROCESSING BERLIN DATASET
	from utilities      import model_circle, reduce_EMData_to_root, bcast_EMData_to_all, dropImage
	from utilities      import bcast_string_to_all, getImage, get_input_from_string
	from utilities      import get_arb_params, set_arb_params, dropSpiderDoc,recv_attr_dict, send_attr_dict
	from utilities      import dropSpiderDoc,get_im
	from filter	    import filt_params, filt_btwl, filt_from_fsc, filt_table, filt_gaussl
	from alignment	    import proj_ali_incore
	from random	    import randint
	from fundamentals   import fshift,rot_avg_image
	import os
	import types
	from string         import replace
	from reconstruction import rec3D_MPI, rec3D_MPI_noCTF
	from mpi 	    import mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	from mpi 	    import mpi_barrier
	
	number_of_proc = mpi_comm_size(MPI_COMM_WORLD)
	myid           = mpi_comm_rank(MPI_COMM_WORLD)
	main_node = 0
	if(myid == main_node):
		if os.path.exists(outdir):  os.system('rm -rf '+outdir)
		os.mkdir(outdir)
        finfo = None
	#info_file = replace("progress%4d"%myid, ' ', '0')
        #finfo = open(info_file, 'w')

	max_iter    = int(maxit)
	xrng        = get_input_from_string(xr)
	if  yr == "-1":  yrng = xrng
	else          :  yrng = get_input_from_string(yr)
	step        = get_input_from_string(ts)
	delta       = get_input_from_string(delta)
	lstp = min( len(xrng), len(yrng), len(step), len(delta) )
	if (an == "-1"):
		an = []
		for i in xrange(lstp):   an.append(-1)
	else:
		from  alignment	    import proj_ali_incore_localB
		an      = get_input_from_string(an)
	first_ring  = int(ir)
	rstep       = int(rs)
	last_ring   = int(ou)
	vol     = EMData()
	vol.read_image(ref_vol)
	nx      = vol.get_xsize()
	if last_ring < 0:	last_ring = int(nx/2) - 2
	if(maskfile):
		if(type(maskfile) is types.StringType): mask3D = getImage(maskfile)
		else:                                  mask3D = maskfile
	else:         mask3D = model_circle(last_ring, nx, nx, nx)
	nima            = EMUtil.get_image_count(stack)
	mask = model_circle(last_ring, nx, nx)
	
	image_start, image_end = MPI_start_end(nima, number_of_proc, myid)

	if(myid == main_node)       :  dropImage(vol, os.path.join(outdir,"ref_volf00.spi"), "s")
	if(CTF):
		ctf_dicts = ["defocus", "Cs", "voltage", "Pixel_size", "amp_contrast", "B_factor", "ctf_applied" ]
		#                 0      1         2            3               4                  5               6
		from reconstruction import rec3D_MPI
	else:
		from reconstruction import rec3D_MPI_noCTF
	from utilities import readSpiderDoc, set_arb_params
	prm = readSpiderDoc("params_new.doc")
	prm_dict = ["phi", "theta", "psi", "s2x", "s2y"]
	for im in xrange(image_start, image_end):
		data[im-image_start].set_attr('ID', im)
		set_arb_params(ima, prm[im], prm_dict)
		if(CTF):
			ctf_params = get_arb_params(data[im], ctf_dicts)
			if(im == image_start): data_had_ctf = ctf_params[6]
			if(ctf_params[6] == 0):
				st = Util.infomask(data[im-image_start], mask, False)
				data[im-image_start] -= st[0]
				from filter import filt_ctf
				data[im-image_start] = filt_ctf(data[im], ctf_params[0], ctf_params[1], ctf_params[2], ctf_params[3], ctf_params[4], ctf_params[5])
				data[im-image_start].set_attr('ctf_applied', 1)
	del prm
	# do the projection matching
	from  string        import replace
	from utilities      import bcast_number_to_all
	from morphology     import adaptive_mask, threshold, threshold_to_minval
	from statistics     import histogram
	from reconstruction import recons3d_nn_SSNR_MPI
	for N_step in xrange(lstp):
 		for Iter in xrange(max_iter):
			#print " ali3d_d_MPI: ITERATION #",N_step*max_iter + Iter+1
			#  We have to find a mask on a filtered volume, apply it to non filtered, filter, 
			#          derive adjustment of rotational average on thresholded filtered volume
			#          finally apply mask and adjustment to not-filtered and fitler it
			#  vol   - filtered
			#  volo  - not-filtered
			#if(N_step == 0 and Iter == 0):
			#	adam = adaptive_mask(vol, 3000, 2.22)
			#	vol = threshold( adam*vol)
			#	h = histogram( vol )
			#	vol *= get_im("rotav_tteftu_with_tRNA.spi") / threshold_to_minval( rot_avg_image(vol), h[len(h)//2])
			#	vol = filt_btwl(vol, 0.3, 0.4)
			if myid == 0:
				[ssnr1, vol_ssnr] = recons3d_nn_SSNR_MPI(myid, data, model_circle(last_ring, nx, nx), ctf = CTF)
				del ssnr1
				#  change volume to fsc
				vol_ssnr /= vol_ssnr + 1.0
				#  filter it somewhat
				vol_ssnr = threshold(filt_gaussl(vol_ssnr, 0.1))
			else:  recons3d_nn_SSNR_MPI(myid, data, model_circle(last_ring, nx, nx), ctf = CTF)

			if(CTF): volo, fscc = rec3D_MPI(data, snr, sym, mask3D, os.path.join(outdir, replace("resolution%4d"%(N_step*max_iter+Iter+1),' ','0')), myid, main_node)
			else:    volo, fscc = rec3D_MPI_noCTF(data, sym, mask3D, os.path.join(outdir, replace("resolution%4d"%(N_step*max_iter+Iter+1),' ','0')), myid, main_node)

			mpi_barrier(MPI_COMM_WORLD)
			if(myid == main_node):
				dropImage(volo,  os.path.join(outdir, replace("vol%4d.spi"%(N_step*max_iter+Iter+1),' ','0')), "s")
				from fundamentals import rot_avg
				filt = filt_from_fsc(fscc, 0.1)
				# This is a cheat - it moves the resolution curve to the right making the filter more lenient
				#filt = [ 1.0, 1.0, 1.0] + filt
				#filt = [ 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] + filt
				rfsc = rot_avg(vol_ssnr)
				rfsc.set_value_at(0, 1.0)
				nrfsc = rfsc.get_xsize()
				for irf in xrange(nrfsc):
					qtq = rfsc.get_value_at(irf)
					if(qtq > 0.0):   rfsc.set_value_at(irf, filt[irf]/qtq)
					else:            rfsc.set_value_at(irf, 0.0)
				vol_ssnr = vol_ssnr.mult_radial(rfsc)  # adjust radially fsc filter to fsc curve
				dropImage(vol_ssnr,  os.path.join(outdir, replace("filter%4d.spi"%(N_step*max_iter+Iter+1),' ','0')), "s")
				#  Filter by volume
				vol = volo.filter_by_image(vol_ssnr)
				#vol  = filt_table(volo, filt)
				if(center == 1):
					cs   = vol.phase_cog()
					vol  = fshift(vol, -cs[0], -cs[1] -cs[2])
					volo = fshift(volo, -cs[0], -cs[1] -cs[2])
				dropImage(vol, os.path.join(outdir, replace("volf%4d.spi"%(N_step*max_iter+Iter+1),' ','0')), "s")
				adam = adaptive_mask(vol, 3000, 2.22)
				vol = threshold( adam*vol )
				h = histogram( vol )
				vol = threshold( adam*volo ) * get_im("rotav_tteftu_with_tRNA.spi") / threshold_to_minval( rot_avg_image(vol), h[len(h)//2])
				del volo
				#  Filter by volume
				vol = vol.filter_by_image(vol_ssnr)
				#vol  = filt_table(vol, filt)
				#vol = filt_btwl(vol, fl, fh)
				dropImage(vol, os.path.join(outdir, replace("vhlf%4d.spi"%(N_step*max_iter+Iter+1),' ','0')), "s")
				del adam, vol_ssnr, rfsc, filt
				del h
			bcast_EMData_to_all(vol, myid, main_node)
			if(an[N_step] == -1): proj_ali_incore(vol, mask3D, data, first_ring, last_ring, rstep, xrng[N_step], yrng[N_step], step[N_step], delta[N_step], ref_a, sym, finfo, MPI=True)
			else:                 proj_ali_incore_localB(vol, mask3D, data, first_ring, last_ring, rstep, xrng[N_step], yrng[N_step], step[N_step], delta[N_step], an[N_step], ref_a, sym, finfo, MPI=True)
			prm = []
			for im in xrange(image_start, image_end):
				prml = get_arb_params(data[im-image_start], prm_dict)
				prml.append(im)
				prm.append(prml)
			dropSpiderDoc(os.path.join(outdir, replace("new_params%8d"%((N_step*max_iter+Iter+1)*1000+myid),' ','0')), prm," phi, theta, psi, s2x, s2y, image number")
			del prm, prml

	# write out headers  and STOP, under MPI writing has to be done sequentially
	mpi_barrier(MPI_COMM_WORLD)
	if(CTF and data_had_ctf == 0):
		for im in xrange(len(data)): data[im].set_attr('ctf_applied', 0)
	#par_str = ['phi', 'theta', 'psi', 's2x', 's2y']
	if(myid == main_node): recv_attr_dict(main_node, stack, data, par_str, image_start, image_end, number_of_proc)
	else: send_attr_dict(main_node, data, par_str, image_start, image_end)

"""
