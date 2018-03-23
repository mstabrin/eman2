import pytest


def test_display_file(qtbot, win):
    win = win('e2display','')
    main_form = win.main_form
    qtbot.addWidget(main_form)

    win.cycle(qtbot, main_form)

# Tabs inspector when Option + LeftClick
# Save
@pytest.mark.skip(reason="Tests not implemented yet")
def test_display_tab_save():
    pass

# Probe
@pytest.mark.skip(reason="Tests not implemented yet")
def test_display_tab_probe():
    pass

# Meas
@pytest.mark.skip(reason="Tests not implemented yet")
def test_display_tab_meas():
    pass

# Draw
@pytest.mark.skip(reason="Tests not implemented yet")
def test_display_tab_draw():
    pass

# PSpec
@pytest.mark.skip(reason="Tests not implemented yet")
def test_display_tab_pspec():
    pass

# Python
@pytest.mark.skip(reason="Tests not implemented yet")
def test_display_tab_python():
    pass
