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

@pytest.fixture
def chaos_recipe(poestash):
    result = lib.find_chaos_recipe_needed(poestash)
    return result

@pytest.fixture
def gemcutter_recipe(poestash):
    return lib.find_gemcutter_needed(poestash)
