import pytest


def test_display_file(qtbot, win):
    win = win('e2display','')
    main_form = win.main_form
    qtbot.addWidget(main_form)

    win.cycle(qtbot, main_form)
