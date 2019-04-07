import pytest

import melbalabs.poexp.lib as lib

@pytest.fixture(scope='session')
def conf():
    return lib.read_conf()

@pytest.fixture(scope='session')
def poesessid(conf):
    return conf['poesessid']

@pytest.fixture(scope='session')
def poestash(poesessid):
    return lib.PoeStash(poesessid)
