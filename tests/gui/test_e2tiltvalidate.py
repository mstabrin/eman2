import os
from PyQt4.QtCore import Qt

def test_cli(qtbot, win, curdir):
    win = win('e2tiltvalidate', os.path.join(curdir, 'data', 'e2tiltvalidate', 'TiltValidate_04'), -1, 360.0, plotdatalabels=False, color='#00ff00', plotzaxiscolor=False)
    
    main_form = win.main_form
    qtbot.addWidget(main_form)
    
    win.cycle(qtbot, main_form)
