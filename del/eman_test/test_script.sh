rm -rf test_00
mkdir test_00
e2simmx.py data/init_ref.hdf data/init_ptcls.hdf test_00/simmx.hdf -f --saveali --cmp=frc:maxres=25.0 --align=rotate_translate_tree --aligncmp=ccc --force --verbose=-1 --ralign=refine --raligncmp=ccc --parallel=thread:12
e2classify.py test_00/simmx.hdf test_00/classmx.hdf -f --sep 1
e2classaverage.py --input init_ptcls.hdf --classmx test_00/classmx.hdf --decayedge --storebad --output test_00/classes.hdf --ref init_ref.hdf --iter 1 -f --resultmx test_00/clsresult.hdf --normproc normalize.edgemean --averager mean --keep 1. --cmp frc:maxres=25 --align rotate_translate_tree --aligncmp ccc --ralign refine --raligncmp ccc --parallel thread:12
e2make3dpar.py --input test_00/classes.hdf --sym d2 --output test_00/threed.hdf --keep 1 --apix 2.55 --pad 208 --mode gauss_5 --threads 12
e2proc3d.py test_00/threed.hdf test_00/threed_lp.hdf --process filter.lowpass.gauss:cutoff_freq=.08 --process normalize