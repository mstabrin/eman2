import os


def test_display_initial_gui(qtbot, win, curdir):
    stack=os.path.join(curdir, "data", "e2spt_wedge", "00bin16.hdf")
    
    win = win('e2spt_wedge', stack, 60.0, 0.05, 0.5)
    main_form = win.main_form

    win.cycle(qtbot, main_form)
