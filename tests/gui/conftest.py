import pytest
from PyQt4.QtGui import QPixmap
import os
import filecmp
from subprocess import check_call


def pytest_configure(config):
    import EMAN2
    EMAN2._called_from_test = True

def pytest_unconfigure(config):
    import EMAN2
    del EMAN2._called_from_test

@pytest.fixture
def curdir(request):
    return request.fspath.dirname

def get_main_form(module_name, *kargs, **kwargs):
    module = __import__(module_name)
    if not os.path.isdir(module_name):
        os.mkdir(module_name)
    main_form = module.main_loop(*kargs, **kwargs)
    return main_form

@pytest.fixture
def main_form():
    # main_form = common.get_main_form()
    return get_main_form
    # main_form.close()

class Win(object):
    def __init__(self, module_name, *kargs, **kwargs):
        self.counter = 0
        self.dir = module_name
        self.main_form = get_main_form(module_name, *kargs, **kwargs)
    
    def cycle(self, qtbot, form, clickButton=None):
        form.raise_()
        form.activateWindow()
        if clickButton:
            qtbot.mouseClick(form, clickButton)
        qtbot.waitForWindowShown(form)
        qtbot.wait(100)
        self.snap(qtbot, form)
    
    def snap(self, qtbot, form):
        fname = '%s.png'%os.path.join(self.dir,str(self.counter))
        qtbot.wait(500)
        qpxmap = QPixmap.grabWindow(form.winId())
        qtbot.wait(500)
        qpxmap.save(fname,'png')
        qtbot.wait(100)

        refs_dir = '/Users/shadow_walker/Files/eclipse_workspace/workspace_work/eman2/tests/gui/refs'
        ref_file = os.path.join(refs_dir, self.dir, str(self.counter) + '.png')
        
        print("{}: {} and {}".format(filecmp.cmp(ref_file, fname), ref_file, fname))
        check_call(["perceptualdiff", ref_file, fname])
        
        self.counter += 1

@pytest.fixture
def win():
    return Win

def display_initial_gui(main_window, snap, curdir):
    def f(module_name, args_file, args_opt, windows):
        args = [os.path.join(curdir, *fname) for fname in args_file] + args_opt
        print(args)
        print(module_name)
        main_window1 = main_window(module_name, args)
        snap1 = snap(module_name)
        for w in windows:
            print(w)
            if w:
                snap1(reduce(getattr, w.split('.'), main_window1))
            else:
                snap1(main_window1)
        # return main_window
    return f
