import os


def test_display_file(qtbot, win, curdir):
    win = win('e2evalimage',[os.path.join(curdir, 'e2evalimage', 'BGal_000232.hdf')])
    main_form = win.main_form
    qtbot.addWidget(main_form)
    
    win.cycle(qtbot, main_form)
    win.cycle(qtbot, main_form.wplot)
    win.cycle(qtbot, main_form.wfft)
    win.cycle(qtbot, main_form.wimage)
