from PyQt4.QtCore import Qt
import os


def test_mouseClick_altModifier(qtbot, win, curdir):
    win = win('e2filtertool','%s'%os.path.join(curdir,'e2display/twod.hdf'))
