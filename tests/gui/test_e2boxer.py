import os
from PyQt4.QtCore import Qt

def test_cli(qtbot, win, curdir):
    win = win('e2boxer', apix=1, imagenames=["1\t%s"%os.path.join(curdir,'e2boxer', 'test_box.hdf')])
