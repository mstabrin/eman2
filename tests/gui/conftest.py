import pytest
import os


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
        self.dir = module_name
        self.main_form = get_main_form(module_name, *kargs, **kwargs)
    
@pytest.fixture
def win():
    return Win
