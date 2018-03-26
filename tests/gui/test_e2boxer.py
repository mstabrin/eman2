import os
from PyQt4.QtCore import Qt

def test_cli(qtbot, win, curdir):
    win = win('e2boxer', apix=1, imagenames=["1\t%s"%os.path.join(curdir,'e2boxer', 'test_box.hdf')], box=32)
    main_form = win.main_form
    qtbot.addWidget(main_form)
    
    win.cycle(qtbot, main_form)
    win.cycle(qtbot, main_form.wimage, Qt.LeftButton)
    win.cycle(qtbot, main_form.wparticles)
