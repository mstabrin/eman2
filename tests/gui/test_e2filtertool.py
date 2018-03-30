from PyQt4.QtCore import Qt
import os


def test_mouseClick_altModifier(qtbot, win, curdir):
    win = win('e2filtertool','%s'%os.path.join(curdir, 'data', 'e2display/twod.hdf'))
    main_form = win.main_form
    qtbot.addWidget(main_form)
    
    win.cycle(qtbot, main_form)
    win.cycle(qtbot, main_form.viewer[0])
    qtbot.mouseClick(main_form.viewer[0], Qt.LeftButton, Qt.AltModifier)
    qtbot.wait(1000)
# Need a set of filters and filter types to test spinboxes, checkboxes and buttons
