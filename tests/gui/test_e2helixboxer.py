from PyQt4.QtCore import Qt
import os


def test_display_initial_gui(qtbot, win, curdir):
    win = win('e2helixboxer', ['%s'%os.path.join(curdir, 'e2boxer', 'test_box.hdf')], 100, "hdf")
    main_form = win.main_form
    
    win.cycle(qtbot, main_form.main_image)
    qtbot.mouseClick(main_form.main_image, Qt.LeftButton)

    # main_window = main_window('e2helixboxer', [os.path.join(curdir, 'e2boxer', 'test_box.hdf'), "--gui"])
    # snap = snap('e2helixboxer')
    # snap(main_window)
    # snap(main_window.main_image)
