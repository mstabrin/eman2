# from PyQt4.QtCore import Qt


def test_display_initial_gui(qtbot, win):
    win = win('e2projectmanager')
    main_form = win.main_form

    win.cycle(qtbot, main_form)
    # qtbot.mouseClick(main_form.main_image, Qt.LeftButton)
