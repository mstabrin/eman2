#!/usr/bin/env python
# Muyuan Chen 2018-04
from EMAN2 import *
import numpy as np
import Queue
import threading

def refine_ali(ids, pinfo, m, jsd, options):
	sz=m["nx"]
	for ii in ids:
		l=pinfo[ii]
		e=EMData(l[1], l[0])
		b=e["nx"]
		e=e.get_clip(Region((b-sz)/2, (b-sz)/2, sz,sz)).process("normalize")
		xf=Transform(eval(l[2]))
		pj=m.project("standard", xf).process("normalize")
		eali=e.align("refine", pj, {"maxshift":8, "maxiter":50}, "frc", {"maxres":options.maxres})
		al=eali["xform.align2d"]
		xf1=al.inverse()*xf

		scr=eali.cmp("frc", pj, {"maxres":options.maxres})
		dc=xf1.get_params("eman")
		dc["score"]=float(scr)
		
		jsd.put((ii, dc))
def main():
	
	usage=" "
	parser = EMArgumentParser(usage=usage,version=EMANVERSION)
	parser.add_argument("--path", type=str,help="path", default=None)
	parser.add_argument("--sym", type=str,help="symmetry", default="c1")
	parser.add_argument("--threads", type=int,help="threads", default=12)
	parser.add_argument("--padby", type=float,help="pad by factor. default is 2", default=2.)
	parser.add_argument("--keep", type=float,help="propotion of tilts to keep. default is 0.5", default=0.5)
	parser.add_argument("--maxres", type=float,help="max resolution for comparison", default=20)
	parser.add_argument("--maxalt", type=float,help="max altitude to insert to volume", default=90)
	parser.add_argument("--iter", type=int,help="iteration", default=1)
	parser.add_argument("--dopostp", action="store_true", default=False ,help="do post process")
	parser.add_argument("--unmask", action="store_true", default=False ,help="use unmasked map as references")

	parser.add_argument("--ppid", type=int,help="ppid...", default=-1)

	(options, args) = parser.parse_args()
	logid=E2init(sys.argv)
	
	path=options.path
	itr=options.iter
	if not path: 
		print("No input path. Exit.")
		return

	js=js_open_dict(path+"/particle_parms_{:02d}.json".format(itr))
	k=js.keys()[0]
	src=eval(k)[0]
	e=EMData(src, 0,True)
	bxsz=e["nx"]
	apix=e["apix_x"]
	print("loading 3D particles from {}".format(src))
	print("box size {}, apix {:.2f}".format(bxsz, apix))
	
	fscs=[os.path.join(path,f) for f in os.listdir(path) if f.startswith("fsc") and f.endswith("{:02d}.txt".format(itr))]
	for f in fscs:
		os.rename(f, f[:-4]+"_raw.txt")
		
	for eo in ["", "_even", "_odd"]:
		os.rename("{}/threed_{:02d}{}.hdf".format(path, itr, eo), 
				"{}/threed_{:02d}_raw{}.hdf".format(path, itr, eo))
	
	lname=[os.path.join(path, "ali_ptcls_{:02d}_{}.lst".format(itr,eo)) for eo in ["even", "odd"]]
	for l in lname:
		try: os.remove(l)
		except:pass
	lst=[LSXFile(m, False) for m in lname]
	
	n3d=len(js.keys())
	for ii in range(n3d):
		e=EMData(src, ii, True)
		fname=e["class_ptcl_src"]
		ids=e["class_ptcl_idxs"]
		ky="('{}', {})".format(src, ii)
		dic=js[ky]
		xali=dic["xform.align3d"]
		for i in ids:
			try:
				m=EMData(fname, i, True)
			except:
				continue
			xf=m["xform.projection"]
			dc=xf.get_params("xyz")
			if abs(dc["ytilt"])>options.maxalt:
				continue
			rot=xf*xali.inverse()
			lst[ii%2].write(-1, i, fname, str(rot.get_params("eman")))
			
	
	
	#fname=src.replace("particles3d", "particles")
	#num=EMUtil.get_image_count(fname)
	#print("Getting {} 2d particles from {}".format(num, fname))
	
	#for ii in range(num):
		#e=EMData(fname, ii, True)
		#pid=e["model_id"]
		#nid=e["tilt_id"]
		#xf=e["xform.projection"]
		#ky="('{}', {})".format(src, pid)
		#dic=js[ky]
		
		#xali=dic["xform.align3d"]
		#rot=xf*xali.inverse()
		#lst[pid%2].write(-1, ii, fname, str(rot.get_params("eman")))
		
	for l in lst:
		l.close()
		
	js=None
	
	for eo in ["even", "odd"]:
		lst=LSXFile("{}/ali_ptcls_{:02d}_{}.lst".format(path, itr, eo), True)
		pinfo=[]
		nptcl=lst.n
		for i in range(nptcl):
			pinfo.append(lst.read(i))
		lst=None
		
		
		if options.unmask:
			m=EMData("{}/threed_{}_unmasked.hdf".format(path, eo))
			m.process_inplace("mask.soft",{"outer_radius":-4})
		else:
			m=EMData("{}/threed_{:02d}_raw_{}.hdf".format(path, itr, eo))
			
		m.process_inplace('normalize')
		#m.process_inplace("threshold.belowtozero",{"minval":0.5})

		jsd=Queue.Queue(0)
		jobs=[]
		print("Refining {} set with {} 2D particles..".format(eo, nptcl))
		batchsz=100
		for tid in range(0,nptcl,batchsz):
			ids=range(tid, min(tid+batchsz, nptcl))
			jobs.append([ids, pinfo, m, jsd, options])

		thrds=[threading.Thread(target=refine_ali,args=(i)) for i in jobs]
		thrtolaunch=0
		tsleep=threading.active_count()

		ndone=0
		dics=[0]*nptcl
		nthrd=12
		while thrtolaunch<len(thrds) or threading.active_count()>tsleep:
			if thrtolaunch<len(thrds):
				while (threading.active_count()==nthrd+tsleep ) : time.sleep(.1)
				thrds[thrtolaunch].start()
				thrtolaunch+=1
			else: time.sleep(.2)


			while not jsd.empty():
				ii, dc=jsd.get()
				dics[ii]=dc
				ndone+=1
				if ndone%2000==0:
					print("\t{}/{} finished.".format(ndone, nptcl))

		for t in thrds: t.join()

		allscr=np.array([d["score"] for d in dics])
		print(np.min(allscr), np.mean(allscr), np.max(allscr), np.std(allscr))
		allscr*=-1
		s=allscr.copy()
		s-=np.mean(s)
		s/=np.std(s)
		clp=2
		ol=abs(s)>clp
		print("Removing {} outliers from {} particles..".format(np.sum(ol), len(s)))
		s=(s+clp)/clp/2
		s[ol]=0
		allscr=s
		
		#allscr-=np.min(allscr)-1e-5
		#allscr/=np.max(allscr)

		lname="{}/ali_ptcls_refine_{:02d}_{}.lst".format(path, itr, eo)
		try: os.remove(lname)
		except: pass
		lout=LSXFile(lname, False)
		for i, d in enumerate(dics):
			d["score"]=float(allscr[i])
			l=pinfo[i]
			lout.write(-1, l[0], l[1], str(d))

		lout=None
		
		pb=options.padby
		cmd="make3dpar_rawptcls.py --input {inp} --output {out} --pad {pd} --padvol {pdv} --threads 12 --outsize {bx} --apix {apx} --mode gauss_2 --keep {kp} --sym {sm}".format(
			inp=lname, 
			out="{}/threed_{:02d}_{}.hdf".format(path, itr, eo),
			bx=bxsz, pd=int(bxsz*pb), pdv=int(bxsz*pb), apx=apix, kp=options.keep, sm=options.sym)
		
		run(cmd)
		
	if options.dopostp:
		sfx="{}/threed_{:02d}".format(path, itr )
		if os.path.isfile("structfac.txt"):
			sf=" --setsf structfac.txt"
		else:
			sf=""
		cmd="e2refine_postprocess.py --even {} --odd {} --output {} --iter {} --mass 1000.0 --restarget 10.0 --sym {}  --align {} ".format(
			sfx+"_even.hdf", sfx+"_odd.hdf", sfx+".hdf", itr, options.sym, sf)
		
		run(cmd)
	
		fscs=[os.path.join(path,f) for f in os.listdir(path) if f.startswith("fsc") and f.endswith("{:02d}.txt".format(itr))]
		for f in fscs:
			os.rename(f, f[:-4]+"_ali.txt")
		
	E2end(logid)
	
def run(cmd):
	print cmd
	launch_childprocess(cmd)
	
	
if __name__ == '__main__':
	main()
	