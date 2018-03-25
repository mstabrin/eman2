import os
from PyQt4.QtCore import Qt

def test_cli(qtbot, win, curdir):
    win = win('e2tiltvalidate', os.path.join(curdir, 'data', 'e2tiltvalidate', 'TiltValidate_04'), -1, 360.0, plotdatalabels=False, color='#00ff00', plotzaxiscolor=False)
    
    --volume 3DmapIP3R1_clip_188apix.mrc 
    --untiltdata Ip3R_particles_02_0deg_ptcls_ctfflip.hdf 
    --tiltdata Ip3R_particles_02_10deg_ptcls_ctfflip.hdf 
    --path TiltValidate_04
    --gui
    main_form = win.main_form
    qtbot.addWidget(main_form)
    
    win.cycle(qtbot, main_form)
