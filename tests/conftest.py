import pytest

import melbalabs.poexp.lib as lib

@pytest.fixture(scope='session')
def conf():
    return lib.read_conf()
