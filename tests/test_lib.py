import time

import pytest
import pyautogui

import melbalabs.poexp.lib as lib

def test_basic(conf):
    assert conf

def test_stash(conf):
    stash = lib.PoeStash(conf['poesessid'])
    assert stash.items

def test_stash_filter(poestash):
    untagged = poestash.get_untagged_items()
    for item in untagged:
        print(item)
        print()

def test_main2(conf):
    recipes, poe_stash = lib.main2(conf)

def test_find_chaos_recipe_needed(poestash):
    chaos_recipe = lib.find_chaos_recipe_needed(poestash)
    print(chaos_recipe)

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
    msg_6s = lib.format_six_socket_items(poestash)
    import pdb;pdb.set_trace()

def test_six_socket_items(poestash):
    print(len(poestash.six_socket_items))
    print(len(poestash.six_link_items))

def test_chromatic_items(poestash):
    print(len(poestash.chromatic_items))

def test_map_items(poestash):
    print(len(poestash.map_items))

def test_divcard_items(poestash):
    print(len(poestash.divcard_items))
    import pdb;pdb.set_trace()

def test_currency_items(poestash):
    print(len(poestash.currency_items))
    items = lib.find_currency_items(poestash)

def test_find_poe():
    poe_found, poe_title = lib.find_poe()
    print(poe_found, poe_title)
