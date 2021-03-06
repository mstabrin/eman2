#!/usr/bin/env python
# Muyuan Chen 2018-04

from EMAN2 import *
import numpy as np
import scipy.spatial.distance as scidist
import Queue
import threading

def main():
	
	usage="A simple template matching script. run [prog] <tomogram> <reference> to extract particles from tomogram. Results will be saved in the corresponding info files and can be visualized via spt_boxer"
	parser = EMArgumentParser(usage=usage,version=EMANVERSION)
	parser.add_argument("--delta", type=float,help="delta angle", default=30)
	parser.add_argument("--dthr", type=float,help="distance threshold", default=16)
	parser.add_argument("--vthr", type=float,help="value threshold (n sigma)", default=2.)
	parser.add_argument("--nptcl", type=int,help="maximum number of particles", default=500)
	(options, args) = parser.parse_args()
	logid=E2init(sys.argv)
	
	imgname=args[0]
	tmpname=args[1]
	sym=parsesym("c1")
	dt=options.delta
	oris=sym.gen_orientations("eman",{"delta":dt, "phitoo":dt})
	print("Try {} orientations.".format(len(oris)))
	m=EMData(tmpname)
	m.process_inplace("math.meanshrink",{'n':2})
	sz=m["nx"]
	img=EMData(imgname)
	img.process_inplace("math.meanshrink",{'n':2})
	img.mult(-1)
	img.process_inplace('normalize')

	hdr=m.get_attr_dict()
	ccc=img.copy()*0-65535

	jsd=Queue.Queue(0)
	thrds=[threading.Thread(target=do_match,args=(jsd, m,o, img)) for o in oris]
	thrtolaunch=0
	tsleep=threading.active_count()

	ndone=0
	while thrtolaunch<len(thrds) or threading.active_count()>tsleep:
		if thrtolaunch<len(thrds) :
			while (threading.active_count()==13 ) : time.sleep(.1)
			thrds[thrtolaunch].start()
			thrtolaunch+=1
		else: time.sleep(1)


		while not jsd.empty():
			cf=jsd.get()
			ccc.process_inplace("math.max", {"with":cf})
			ndone+=1
			if ndone%10==0:
				print("{}/{} finished.".format(ndone, len(oris)))
	
	cbin=ccc.process("math.maxshrink", {"n":2})
	cc=cbin.numpy().copy()
	cshp=cc.shape
	ccf=cc.flatten()
	asrt= np.argsort(-ccf)
	pts=[]
	vthr=np.mean(ccf)+np.std(ccf)*options.vthr
	
	dthr=options.dthr/4
	scr=[]
	#print vthr,cc.shape
	for i in range(len(asrt)):
		aid=asrt[i]
		pt=np.unravel_index(aid, cshp)
		if len(pts)>0:
			dst=scidist.cdist(pts, [pt])
			if np.min(dst)<dthr:
				continue

		pts.append(pt)
		scr.append(float(ccf[aid]))
		if cc[pt]<vthr:
			break
			
	pts=np.array(pts)
	print("Found {} particles".format(len(pts)))
	js=js_open_dict(info_name(imgname))
	n=min(options.nptcl, len(pts))
	if js.has_key("class_list"):
		clst=js['class_list']
		kid=max([int(k) for k in clst.keys()])+1
	else:
		clst={}
		kid=0
		
	clst[str(kid)]={"boxsize":sz*4, "name":base_name(tmpname)}
	js["class_list"]=clst
	if js.has_key("boxes_3d"):
		bxs=js["boxes_3d"]
	else:
		bxs=[]
	bxs.extend([[p[2], p[1],p[0], 'tm', scr[i] ,kid] for i,p in enumerate(pts[:n]*4)])
	js['boxes_3d']=bxs
	js.close()
	E2end(logid)
	
def do_match(jsd, m, o, img):
	e=m.copy()
	e.transform(o)
	cf=img.calc_ccf(e)
	cf.process_inplace("xform.phaseorigin.tocenter")
	jsd.put(cf)

def run(cmd):
	print cmd
	launch_childprocess(cmd)
	
	
if __name__ == '__main__':
	main()
	