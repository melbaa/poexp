import time
import pyautogui

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

def test_find_chaos_recipe_needed(poestash):
    chaos_recipe = lib.find_chaos_recipe_needed(poestash)

def test_find_gemcutter_needed(poestash):
    gemcutter = lib.find_gemcutter_needed(poestash)
    import pdb;pdb.set_trace()
