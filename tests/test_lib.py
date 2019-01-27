import time

import melbalabs.poexp.lib as lib

def test_basic(conf):
    assert conf

def test_stash(conf):
    stash = lib.PoeStash(conf['poesessid'])
    assert stash.items

def test_main2(conf):
    chaos_recipe = lib.main2(conf)

def test_click(conf):
    chaos_recipe = lib.main2(conf)
    lib.move_ready_items_to_inventory(chaos_recipe)
