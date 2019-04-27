import time

import pytest
import pyautogui

import melbalabs.poexp.lib as lib

def test_basic(conf):
    assert conf

def test_stash(conf):
    stash = lib.PoeStash(conf['poesessid'])
    assert stash.items

def test_main2(conf):
    chaos_recipe = lib.main2(conf)

def test_find_chaos_recipe_needed(poestash):
    chaos_recipe = lib.find_chaos_recipe_needed(poestash)

@pytest.mark.skip(reason='need to update with gem recipe, how to test clicks')
def test_click(conf, chaos_recipe):
    lib.move_ready_items_to_inventory(chaos_recipe)

def test_find_gemcutter_needed(poestash):
    gemcutter = lib.find_gemcutter_needed(poestash)
    assert gemcutter.ready

def test_format_chaos_recipe(chaos_recipe, gemcutter_recipe, poestash):
    msg_chaos = lib.format_chaos_recipe(chaos_recipe, colorize=False)
    msg_ident = lib.format_identified_items(poestash)
    msg_gcp = lib.format_gemcutter_recipe(gemcutter_recipe)
    import pdb;pdb.set_trace()

