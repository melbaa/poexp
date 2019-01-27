import melbalabs.poexp.lib as lib

def test_basic(conf):
    assert conf

def test_stash(conf):
    stash = lib.PoeStash(conf['poesessid'])
    assert stash.items

def test_main2(conf):
    recipe = lib.main2(conf)
    print(recipe)


