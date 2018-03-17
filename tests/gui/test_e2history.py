from PyQt4.QtCore import Qt


def test_okButton(qtbot, win):
    win = win('e2history')
    main_form = win.main_form
    
    win.cycle(qtbot, main_form.form)
    qtbot.mouseClick(main_form.form.layout().itemAt(1).itemAt(1).widget(), Qt.LeftButton)
