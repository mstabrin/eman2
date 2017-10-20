#!/usr/bin/env python
# Muyuan Chen 2017-10
from EMAN2 import *
import numpy as np


def test_simmx(options, path):
	print "--------------------------"
	print "Similarity matrix..."
	cmd="e2simmx.py {} {} {}/simmx.hdf -f --saveali --cmp=frc:maxres=25.0 --align=rotate_translate_tree --aligncmp=ccc --force --verbose=0 --ralign=refine --raligncmp=ccc --parallel=thread:{}".format(options.cls, options.ptcls, path, options.threads)
	run(cmd)
	e0=EMData("{}/simmx.hdf".format(path),0)
	if options.ref:
		e1=EMData("{}/simmx.hdf".format(options.ref), 0)
		e0.sub(e1)
		e2=e0.absi()
		print "{:.3f}, {:.3f}".format(e2["mean"], e2["maximum"])
	else:
		e2=e0.absi()
		print "{:.3f}, {:.3f}".format(e2["mean"]-.241, e2["maximum"]-.539)

def main():
	
	usage="Test EMAN2 functionalities.. "
	parser = EMArgumentParser(usage=usage,version=EMANVERSION)
	parser.add_argument("--path", type=str,help="path", default="")
	parser.add_argument("--ptcls", type=str,help="particles", default="data/init_ptcls.hdf")
	parser.add_argument("--cls", type=str,help="class averages", default="data/init_ref.hdf")
	parser.add_argument("--ref", type=str,help="reference results", default=None)
	parser.add_argument("--testqt", type=int,help="test qt (0/1). default is 1.", default=1)
	parser.add_argument("--testtheano", type=int,help="test theano (0/1). default is 1.", default=1)
	parser.add_argument("--threads", type=int,help="thread", default=12)
	(options, args) = parser.parse_args()
	logid=E2init(sys.argv)
	
	t0=time.time()
	if options.path=="":
		for i in range(100):
			path="test_{:02d}".format(i)
			try:
				os.mkdir(path)
			except:
				pass
			else:
				break
	else:
		path=options.path
	print "Writing output files in {}".format(path)
	print "Outputs should all be 0 or near 0 values..."
	
	print "--------------------------"
	print "File reading/writing.."
	nptcl=EMUtil.get_image_count(options.ptcls)
	nref=EMUtil.get_image_count(options.cls)
	e0=EMData(options.ptcls,0)
	nx=e0["nx"]
	print "{:.3f}, {:.3f}, {:.3f}, {:.3f}".format(nptcl-185, nref-8, nx-120, e0["maximum"]-3.565)

	if options.testqt>0:
		print "--------------------------"
		print "Qt and GL support.."
		from PyQt4 import QtGui
		from PyQt4.QtCore import QTimer
		from emapplication import EMApp
		from emimage import EMImageWidget
		
		class test_window(QtGui.QMainWindow):
			def __init__(self, app, options):
				QtGui.QWidget.__init__(self)
				e=EMData(options.cls)
				imgview = EMImageWidget(data=e, app=app)
				imgview.show()
				if options.ref:
					d=EMData("{}/threed.hdf".format(options.ref))
				else:
					d=test_image_3d()
				d3view=EMImageWidget(data=d, app=app)
				d3view.show()
				
				QTimer.singleShot(500, self.tick)
				
			def tick(self):
				app.quit()
				
				
		app = EMApp()
		twin=test_window(app,options)
		twin.show()
		app.exec_()

		print "--------------------------"
		print "Numpy support..."
		m0=e0.numpy()
		print "{:.3f}, {:.3f}, ".format(m0[nx/2, nx/2]-1.38199, e0[nx/2, nx/2]-1.38199),
		m0[nx/2, nx/2]=0
		print "{:.3f}, {:.3f}, ".format(m0[nx/2, nx/2], e0[nx/2, nx/2]),
		m1=m0+1
		e1=from_numpy(m1)
		print "{:.3f}, ".format(e1[nx/2, nx/2]-1)
	
	
	if options.testtheano>0:
		print "--------------------------"
		print "Testing Theano and GPU support..."
		print "Currently EMAN only works with CUDA backend (instead of gpuarray)..."
		
		import theano
		import theano.tensor as T
		from theano.tensor.nnet import conv
		print "If GPU is activated, the previous line should start with \"Using gpu device X...\""
		
		### matrix multiplication
		a=theano.shared(np.ones((10,10),  dtype=theano.config.floatX))
		b=theano.shared(np.ones((10,10),  dtype=theano.config.floatX))
		c=T.sum(T.dot(a,b))-1000.
		
		### convolution
		a=theano.shared(np.ones((1,1, 10,10), dtype=theano.config.floatX))
		b=theano.shared(np.ones((1,1, 5,5), dtype=theano.config.floatX))
		conv_out = conv.conv2d(
					input=a,
					filters=b,
					filter_shape=(1,1,5,5),
					#image_shape=self.image_shape.eval(),
					border_mode='full'
				)
		
		print "{:.3f}, {:.3f}".format(float(c.eval()), float(np.sum(conv_out.eval())-2500.))

	test_simmx(options, path)
	
	print "--------------------------"
	print "Classification..."
	cmd="e2classify.py {}/simmx.hdf {}/classmx.hdf -f --sep 1".format(path, path)
	run(cmd)
	e0=EMData("{}/classmx.hdf".format(path),0)
	if options.ref:
		e1=EMData("{}/classmx.hdf".format(options.ref), 0)
		e0.sub(e1)
		e2=e0.absi()
		print "{:.3f}, {:.3f}".format(e2["mean"], e2["maximum"])
	else:
		e2=e0.absi()
		print "{:.3f}, {:.3f}".format(e2["mean"]-2.962, e2["maximum"]-7.)
	
	
	print "--------------------------"
	print "Class averaging..."
	cmd="e2classaverage.py --input {} --classmx {}/classmx.hdf --decayedge --storebad --output {}/classes.hdf --ref {} --iter 1 -f --resultmx {}/clsresult.hdf --normproc normalize.edgemean --averager mean --keep 1. --cmp frc:maxres=25 --align rotate_translate_tree --aligncmp ccc --ralign refine --raligncmp ccc --parallel thread:{}".format(
		options.ptcls, path, path, options.cls, path, options.threads)
	run(cmd)
	for i in range(nref):
		e0=EMData("{}/classes.hdf".format(path),0)
		if options.ref:
			e1=EMData("{}/classes.hdf".format(options.ref), 0)
			e0.sub(e1)
			e2=e0.absi()
			print "{:.3f}".format(e2["maximum"]),
		else:
			e2=e0.absi()
			print "{:.3f}".format(e2["maximum"]-8.555),
	print 

	print "--------------------------"
	print "Making 3D..."
	cmd="e2make3dpar.py --input {}/classes.hdf --sym d2 --output {}/threed.hdf --keep 1 --apix 2.55 --pad 208 --mode gauss_5 --threads {}".format(path, path, options.threads)
	run(cmd)
	e0=EMData("{}/threed.hdf".format(path))
	if options.ref:
		e1=EMData("{}/threed.hdf".format(options.ref))
		e0.sub(e1)
		e2=e0.absi()
		print "{:.5f}, {:.5f}".format(e2["mean"], e2["maximum"])
	else:
		e2=e0.absi()
		print "{:.5f}, {:.5f}".format(e2["mean"]-0.032509, e2["maximum"]-0.49397)
	
	print "--------------------------"
	print "Post processing..."
	cmd="e2proc3d.py {}/threed.hdf {}/threed_lp.hdf --process filter.lowpass.gauss:cutoff_freq=.08 --process normalize".format(path, path)
	run(cmd)
	e0=EMData("{}/threed_lp.hdf".format(path))
	if options.ref:
		e1=EMData("{}/threed_lp.hdf".format(options.ref))
		e0.sub(e1)
		e2=e0.absi()
		print "{:.5f}, {:.5f}".format(e2["mean"], e2["maximum"])
	else:
		
		e2=e0.absi()
		print "{:.5f}, {:.5f}".format(e2["mean"]-.579779, e2["maximum"]-13.88037)
	
	
	print "Done. Time elapse: {:.3f}s".format(float(time.time()-t0))
	
	E2end(logid)

def run(cmd):
	print cmd
	launch_childprocess(cmd)
	

if __name__ == '__main__':
	main()
