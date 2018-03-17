import os


def test_display_file(qtbot, win, curdir):
    win = win('e2evalimage',[os.path.join(curdir, 'e2evalimage', 'BGal_000232.hdf')])
