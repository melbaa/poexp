import time
import traceback
import collections
import json

import requests
import colorama
import win32api
import win32gui
import pyautogui

# NOTE: stash and inventory updates on instance change (self or other player) or after a long timeout

# TODO empty dump tab priority. how to free most space: 6s (only 4 to 6 items) -> chaos recipe -> gcp recipe -> currency -> div cards (10 or more)
# maybe use a generator, so each time + is clicked, move to next type. how to reset on stash update?

# TODO unknown items shouldn't be part of chaos recipe
# TODO pick up div cards from dump tab. only when 10+ stacks
# TODO pick up maps from dump tab. only when 10+
# TODO pick up uniques from dump tab
# TODO gemcutter solve use a SMT/SAT solver (z3, pySMT, pySAT)
# TODO currency stash scan
# TODO 4 x 6 socket items stash scan. skip 6l
# TODO chaos recipe sounds change based on needed items. create symlinks and use atomic rename
# See ReplaceFile() and MoveFileEx and use the MOVEFILE_REPLACE_EXISTING and MOVEFILE_WRITE_THROUGH
# TODO six link items handling? see PoeStash.six_link_items
# TODO UI show price of exalt, regal, alch, chisel, fusing in chaos (from poe.watch API or poe.ninja or currency.poe.trade)
# TODO UI show rank
# TODO UI needed items colored like item filter

# -- LOW PRIORITY / NEVER --
# TODO the stuff that return recipes should return lists of recipes, so it's possible to complete multiple recipes in a single update
# TODO UI movable window + save state (where it was, its size)
# TODO make installer with fbs
# TODO button or hotkey for chaos recipe overlay drawing over inventory screen, disappears after a few sec
# could be useful for manual chaos recipe

# FEATURE track xp/hr in 15/45/135min increments
# FEATURE time remaining to level up for levels >= 90
# FEATURE xp to next and previous rank (how much someone is leading or trailing)
# FEATURE UI shows current counts of each chaos recipe item
# FEATURE UI shows needed/missing items to complete eg. 5 chaos recipes
# FEATURE UI chaos recipe button moves 1 completed recipe to inventory
# basically does item sorting for you
# FEATURE UI chaos recipe button becomes + only if there's enough items AND there are enough
# stash items after an API update. In other words, the + should clear after
# it was clicked until an API update (small unavoidable race condition - API updates
# while chaos items are being moved out of stash tab for a recipe leading to incorrect counts)
# FEATURE UI button becomes o when clicked to show we are waiting for an API update with new items
# FEATURE UI warning when dump tab contains some unknown and identified items
# FEATURE UI always on top
# FEATURE UI right click quit menu
# FEATURE don't poll APIs when POE is not found
# FEATURE poestash should tag items when it categorizes them, so the uncategorized ones can be counted. eg 'poexp_found' = True
# FEATURE poestash categorizes items for different recipes
# FEATURE gemcutter recipe stash scan and clicker. 20 qual single and 40 qual multi gem
# FEATURE gems don't count as identified items that should be removed from dump tab
# FEATURE gcp count in info bar
# FEATURE stash count 6s and 6l items
# FEATURE click 6s items, skip 6l
# FEATURE chromatics items (rgb) should be moved to inventory when 5+. only normal and magic items < 6 sockets

txtpath = r"C:\users\melba\desktop\desktop\poerank.txt"
ACCOUNT = "emfan"


# see active leagues with http://api.pathofexile.com/leagues
#LEAGUE = "Abyss"
#LEAGUE = "Bestiary"
#LEAGUE = "Incursion"
#LEAGUE = "Delve"
#LEAGUE = "Betrayal"
LEAGUE = "Synthesis"
LEAGUE = "Synthesis Event (SRE001)"
LEAGUE = "Standard"
LEAGUE = 'Legion'


SLEEP_SEC = 15  # sec

league_active_rank_url = "http://api.pathofexile.com/ladders/{league}?accountName={account}"
prev_next_url = "http://api.pathofexile.com/ladders/{league}?limit=3&offset={offset}"

stash_url = "https://www.pathofexile.com/character-window/get-stash-items?accountName={account}&tabIndex={tabindex}&league={league}&tabs={tabs}"


MAX_QUEUE_LEN = 2000
BASE_TIME_MEASURE_MINUTES = 15
time_measures_per_min = [
    (collections.deque(maxlen=MAX_QUEUE_LEN), 3**0 * BASE_TIME_MEASURE_MINUTES),
    (collections.deque(maxlen=MAX_QUEUE_LEN), 3**1 * BASE_TIME_MEASURE_MINUTES),
    (collections.deque(maxlen=MAX_QUEUE_LEN), 3**2 * BASE_TIME_MEASURE_MINUTES),
]

xp_per_level = {
    90: 1934009687,
    91: 2094900291,
    92: 2268549086,
    93: 2455921256,
    94: 2876116901,
    95: 3111280300,
    96: 3364828162,
    97: 3638186694,
    98: 3932818530,
    99: 4250334444,
}

CHAOS_RECIPE_ITEM_CLASSES = [
    'helmet',
    'boots',
    'gloves',
    'ring',
    'amulet',
    'belt',
    'weapons',
    'chest',
]

ITEM_COLORS_CLI = {
    'helmet': colorama.Fore.BLUE,
    'boots': colorama.Fore.CYAN,
    'gloves': colorama.Fore.YELLOW,
    'ring': colorama.Fore.MAGENTA,
    'amulet': colorama.Fore.GREEN,
    'belt': colorama.Fore.GREEN,
    'weapons': colorama.Fore.RED,
    'chest': colorama.Fore.RED,
}

ITEM_CHAOS_RECIPE_MULTIPLIER = {
    'ring': 2,
}


ChaosRecipe = collections.namedtuple('ChaosRecipe', [
    'need', 'unknown', 'counts', 'ready', 'ready_count',
])
GemcutterRecipe = collections.namedtuple('GemcutterRecipe', [
    'ready', 'ready_20qual', 'total_quality', 'ready_count',
])
SixSocketRecipe = collections.namedtuple('SixSocketRecipe', [
    'ready',
])
ChromaticRecipe = collections.namedtuple('ChromaticRecipe', [
    'ready',
])

class LoginException(RuntimeError):
    pass

class PoeNotFoundException(RuntimeError):
    pass



STASH_FRAME_TYPE = {
    'normal': 0,
    'magic': 1,
    'rare': 2,
    'unique': 3,
    'gem': 4,
    'currency': 5,
    'divination card': 6,
    'quest item': 7,
    'prophecy': 8,
    'relic': 9,
}

def get_quality(item):
    for prop in item['properties']:
        if prop['name'] == 'Quality':
            qual = prop['values'][0][0]  # eg 12%
            qual = qual[1:-1]
            return int(qual)
    return 0

def get_gem_level(item):
    for prop in item['properties']:
        if prop['name'] == 'Level':
            level = prop['values'][0][0]  # eg 20 (Max)
            level = level.split(' ')[0]
            return int(level)
    return 0


POEXP_TAG_FOUND = 'poexp_found'

def tag_found(item):
    item[POEXP_TAG_FOUND] = True

def is_tag_found(item):
    return item.get(POEXP_TAG_FOUND)


def item_socket_groups(item):
    # if there's only 1 group, the item is fully linked
    groups = set()
    for socket in item['sockets']:
        groups.add(socket['group'])
    return groups



class PoeStash:
    # https://pathofexile.gamepedia.com/Public_stash_tab_API#items

    def __init__(self, poesessid):
        # note first tab in inventory
        url = stash_url.format(league=LEAGUE, account=ACCOUNT, tabindex=0, tabs=0)
        resp = requests.get(url, cookies={'POESESSID': poesessid})
        j = resp.json()
        if 'error' in j:
            raise LoginException(j['error']['message'])
        self.raw = j
        self.items = j['items']
        self.chaos_recipe_items = self.get_chaos_recipe_items()
        self.gemcutter_recipe_items = self.get_gemcutter_recipe_items()
        self.six_socket_items, self.six_link_items = self.get_six_socket_items()
        self.chromatic_items = self.get_chromatic_items()
        self.identified_items = self.get_identified_items()

    def get_chromatic_items(self):
        items = []
        for item in self.items:
            if is_tag_found(item):
                continue
            if 'sockets' not in item:
                continue
            if len(item['sockets']) < 3:
                continue
            if len(item['sockets']) == 6:
                continue
            sockets = collections.defaultdict(set)
            for group in item['sockets']:
                group_id = group['group']
                sockets[group_id].add(group['sColour'])

            for group in sockets.values():
                if len(group) >= 3:
                    items.append(item)

        return items


    def get_identified_items(self):
        items = []
        for item in self.items:
            if item['identified'] and not is_tag_found(item):
                tag_found(item)
                items.append(item)
        return items

    def get_six_socket_items(self):
        six_socket = []
        six_link = []
        for item in self.items:
            if is_tag_found(item):
                continue
            if 'sockets' not in item:
                continue
            if len(item['sockets']) != 6:
                continue
            socket_groups = item_socket_groups(item)
            if len(socket_groups) == 1:
                six_link.append(item)
            else:
                six_socket.append(item)
            tag_found(item)
        return six_socket, six_link

    def get_chaos_recipe_items(self):
        """
        a chaos recipe item is rare, unid, wep/armor/accessory
        at least 10 qual
        """
        items = []
        for item in self.items:
            if item['identified']:
                continue
            category = list(item['category'].keys())[0]
            if category not in {'weapons', 'accessories', 'armour'}:
                continue
            if item['frameType'] != STASH_FRAME_TYPE['rare']:
                continue
            tag_found(item)
            items.append(item)
        return items

    def get_gemcutter_recipe_items(self):
        """
        gems with quality > 0
        skip enlighten, empower, enhance
        """
        items = []
        for item in self.items:
            category = list(item['category'].keys())[0]
            if category != 'gems':
                continue
            if item['typeLine'] in {'Enlighten Support', 'Empower Support', 'Enhance Support'}:
                continue
            quality = get_quality(item)
            if quality == 0:
                continue
            gem_level = get_gem_level(item)
            if gem_level >= 20 and quality >= 20:
                # we would rather sell those on the market
                continue
            tag_found(item)
            items.append(item)
        return items



def compute_xph(time_measures_per_min, time_now, level_now, experience_now):
    """
    compute xph in for each time_measure_per_min deque
    keep only `max minutes` measures in the respective queue
    """

    xph = [0.0] * 3
    hours_remaining = [0.0] * 3

    for idx, time_measures_and_minutes in enumerate(time_measures_per_min):

        time_measures, max_minutes = time_measures_and_minutes
        # get rid of old measurements, because they are old or a different level
        while len(time_measures) and (time_measures[0][0] < (time_now - 60 * max_minutes) or time_measures[0][2] != level_now):
            time_measures.popleft()

        if len(time_measures) <= 2:
            continue  # nothing to update


        first = time_measures[0]
        last = time_measures[-1]

        time_diff = last[0] - first[0]
        xp_diff = last[1] - first[1]

        xph[idx] = (xp_diff / time_diff) * 60 * 60
        if xph[idx] and level_now in xp_per_level:  # can be zero
            hours_remaining[idx] = (xp_per_level[level_now] - experience_now) / xph[idx]

        xph[idx] = round(xph[idx] / 1000000, 2)
        hours_remaining[idx] = round(hours_remaining[idx], 1)
    return xph, hours_remaining


def write_file(path, txt):
    with open(path, 'w') as f:
        f.write(txt)

def get_prev_next_xp(rank):
    # ignores the case when leading, cuz never leading :)
    url = prev_next_url.format(league=LEAGUE, account=ACCOUNT, offset=rank-2)
    resp = requests.get(url).json()
    entries = resp['entries']
    prev_xp = entries[0]['character']['experience']
    my_xp = entries[1]['character']['experience']
    next_xp = entries[2]['character']['experience']

    prev_xp_diff = (prev_xp - my_xp)//1000  # in K
    next_xp_diff = (my_xp - next_xp)//1000
    return prev_xp_diff, next_xp_diff


class StashClicker:
    def __init__(self):
        # limit how fast we are clickin
        pyautogui.PAUSE = 0.05  # default 0.1

        # quad tab is this many boxes wide and tall
        self.num_boxes = 24

        # a box is this many pixels wide
        # y 175 745
        self.quad_tab_box_pixels_x = 25
        self.quad_tab_box_pixels_y = 25
        # quad tab inventory coords start in top left
        self.x_start = 20
        self.y_start = 176

        self.y_end = self.y_start + self.quad_tab_box_pixels_y * self.num_boxes

    def click_item(self, item):
        x = self.x_start + self.quad_tab_box_pixels_x * (item['x'])
        y = self.y_start + self.quad_tab_box_pixels_y * (item['y'])
        print('mouse move to', x, y, item['x'], item['y'], item['category'])
        pyautogui.moveTo(x, y)
        pyautogui.keyDown('ctrl')
        pyautogui.click()
        pyautogui.keyUp('ctrl')



def move_ready_items_to_inventory(chaos_recipe, gemcutter_recipe, six_socket_recipe, chromatic_recipe):
    # the generator yields remaining recipes

    stash_clicker = StashClicker()

    # 6s
    if not is_recipe_ready(six_socket_recipe):
        print('not enough 6s items')
    else:
        for item in six_socket_recipe.ready:
            stash_clicker.click_item(item)
        # inventory is likely full at this point
        yield chaos_recipe, gemcutter_recipe, None, chromatic_recipe

    # chromatics
    if not is_recipe_ready(chromatic_recipe):
        print('not enough chromatic items')
    else:
        for item in chromatic_recipe.ready:
            stash_clicker.click_item(item)
        yield chaos_recipe, gemcutter_recipe, None, None

    # chaos recipe
    if not is_recipe_ready(chaos_recipe):
        print ('not enough chaos recipe items to complete recipe')
    else:
        for item_class in CHAOS_RECIPE_ITEM_CLASSES:
            for repeat in range(ITEM_CHAOS_RECIPE_MULTIPLIER.get(item_class, 1)):
                items = chaos_recipe.ready[item_class]
                item = items[repeat]
                stash_clicker.click_item(item)

    # gemcutter recipe
    if not is_recipe_ready(gemcutter_recipe):
        print('not enough gemcutter items to complete recipe')
    else:
        for item in gemcutter_recipe.ready_20qual:
            stash_clicker.click_item(item)

        for item in gemcutter_recipe.ready:
            stash_clicker.click_item(item)

    yield None, None, None, None


def find_gcp_needed(stash):
    """
    single gem 20 qual
    multiple gems 40 qual total
    """
    return


def find_chaos_recipe_needed(stash):
    MAX_NEEDED = 4
    counts = {
        k: 0
        for k in CHAOS_RECIPE_ITEM_CLASSES
    }

    ready_items = {
        k: []
        for k in CHAOS_RECIPE_ITEM_CLASSES
    }

    unknown = []
    for item in stash.chaos_recipe_items:
        category = list(item['category'].keys())[0]
        if category == 'weapons':
            counts[category] += 1
            ready_items[category].append(item)
        elif category in {'accessories', 'armour'}:
            item_class = item['category'][category][0]
            counts[item_class] += 1
            ready_items[item_class].append(item)
        else:
            unknown.append(item)
            raise RuntimeError('unknown item ' + item)

    need = []
    for name, count in counts.items():
        if count < MAX_NEEDED:
            need.append(name)

    ready_count = min(
        len(ready_items[k]) // ITEM_CHAOS_RECIPE_MULTIPLIER.get(k, 1) for k in CHAOS_RECIPE_ITEM_CLASSES
    )
    for k in CHAOS_RECIPE_ITEM_CLASSES:
        adjusted_count = ready_count * ITEM_CHAOS_RECIPE_MULTIPLIER.get(k, 1)
        ready_items[k] = ready_items[k][:adjusted_count]

    return ChaosRecipe(need, unknown, counts, ready_items, ready_count)

def format_chaos_recipe(chaos_recipe, colorize: bool):
    # broken with powershell, works with default terminal or conemu
    # not enough colors

    need, unknown, counts, ready_items, ready_count = chaos_recipe

    need_output = []
    for item in need:
        if item in ITEM_COLORS_CLI and colorize:
            item = ITEM_COLORS_CLI[item] + item + colorama.Style.RESET_ALL
        need_output.append(item)

    adjusted_counts = {
        k: counts[k] / ITEM_CHAOS_RECIPE_MULTIPLIER.get(k, 1)
        for k in CHAOS_RECIPE_ITEM_CLASSES
    }
    chaos_recipe_cli_txt = '''\
need:{}, unk:{} | \
r:{ring:g} a:{amulet:g} b:{belt:g} | \
h:{helmet:g} b:{boots:g} g:{gloves:g} w:{weapons:g} c:{chest:g}'''.format(
            ', '.join(need_output),
            unknown,
            **adjusted_counts,
    )
    return chaos_recipe_cli_txt

def format_identified_items(stash):
    MAX_SHOWN = 5
    identified = []
    for item in stash.identified_items:
        identified.append(item['typeLine'])
    identified_shown = identified[:MAX_SHOWN]
    msg = 'id: {}'.format(identified_shown)
    if len(identified) > MAX_SHOWN:
        msg += ' + {} more'.format(len(identified) - MAX_SHOWN)
    return msg

def format_six_socket_items(stash):
    count = len(stash.six_socket_items)
    msg = '6s: {}'.format(count)
    return msg

class GemSolver:

    """
    a solution is a list of items
    the best solution is as close to 40 as possible. in case of ties, take the one with less items

    an optimization is to prune the solutions after each item. do it in case of
    MemoryError or measurable performance impact
    """

    def __init__(self, items, quality_min, quality_max, num_items_max):
        self.items = items
        self.quality_min = quality_min
        self.quality_max = quality_max
        self.num_items_max = num_items_max

    @staticmethod
    def solution_quality(solution):
        if not solution:
            return 0

        return sum(get_quality(i) for i in solution)

    def is_solution(self, solution):
        return self.quality_min <= self.solution_quality(solution) < self.quality_max and len(solution) <= self.num_items_max


    def build_candidate_solutions(self):
        items = self.items
        candidate_solutions = []
        for item in items:

           # duplicate existing solutions without the item, so we get combinations without the item
            duplicate_solutions = []

            # add to existing solutions
            for candidate_solution in candidate_solutions:
                if self.solution_quality(candidate_solution) < self.quality_min and len(candidate_solution) < self.num_items_max:
                    duplicate_solutions.append(list(candidate_solution))
                    candidate_solution.append(item)

            candidate_solutions.extend(duplicate_solutions)

            # start a new candidate solution with this item
            candidate_solutions.append([item])

        print('gemcutter candidate_solutions', len(candidate_solutions))
        return candidate_solutions

    def find_min_solution(self):
        solutions = self.build_candidate_solutions()

        # find an inital solution to compare to
        for solution in solutions:
            if self.is_solution(solution):
                best = solution
                break
        else:
            return None

        for solution in solutions:
            if self.is_solution(solution):
                if self.solution_quality(solution) < self.solution_quality(best):
                    best = solution
                elif self.solution_quality(solution) == self.solution_quality(best) and len(solution) < len(best):
                    best = solution
        return best




def find_gemcutter_needed(stash):
    """
    20 qual gems go in ready_20qual

    smaller gems in items
    10 11 12 13 14 15 16 17 18 19

    possible algorithms
    - greedy knapsack
    - coin change-making
    - min-coin-chainge
        https://www.algorithmist.com/index.php/Min-Coin_Change
        https://www.geeksforgeeks.org/find-minimum-number-of-coins-that-make-a-change/
    - package-merge, but not enough items to be worth it
    - bruteforce all 3-tuples and 4-tuples
    - all combinations - check all candidate solutions for closest to QUALITY_NEEDED
    for 40 items, it's (40 choose 3) + (40 choose 4) = 101270 possible solutions

    we don't know the distribution of qualities dropping

    we are looking for a solution where the quality of the gems is
    40 <= solution < (40 + smallest gem qual in filter, currently 10 and above)
    and the number of gems is between 3 and 4 to be close to chaos recipe
    3 <= num_gems_used <= 4

    in other words, 3 or 4 gems, as close to 40 qual as possible

    solutions are eg
    14 + 16 + 10
    10 + 10 + 10 + 10
    19 + 19 + 2

    """

    QUALITY_PERFECT = 20
    QUALITY_NEEDED = 40
    NUM_ITEMS_MAX = 4
    total_quality = 0
    ready_count = 0
    ready_20qual = []

    items = []
    for item in stash.gemcutter_recipe_items:
        quality = get_quality(item)
        if quality == QUALITY_PERFECT:
            ready_count += 1
            ready_20qual.append(item)
        else:
            total_quality += get_quality(item)
            items.append(item)

    solver = GemSolver(
        items=items,
        quality_min=QUALITY_NEEDED,
        quality_max=QUALITY_NEEDED+10,
        num_items_max=NUM_ITEMS_MAX,
    )
    solution = solver.find_min_solution()
    if solution:
        ready_count += 1

    return GemcutterRecipe(ready=solution, ready_20qual=ready_20qual, total_quality=total_quality, ready_count=ready_count)

def format_gemcutter_recipe(gemcutter_recipe):
    msg = 'gcp: {}'.format(gemcutter_recipe.ready_count)
    return msg

def find_poe():

    def callback(hwnd, hwnds):
        hwnds.append(hwnd)
        return True

    found = False
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    for h in hwnds:
        title = win32gui.GetWindowText(h).lower()
        if 'exile' in title:
            found = True

    return found

def find_six_sockets(poe_stash):
    MIN_ITEMS = 5  # min worth selling
    MAX_ITEMS = 6  # max to fit in inventory
    if len(poe_stash.six_socket_items) < MIN_ITEMS:
        return SixSocketRecipe(ready=[])
    return SixSocketRecipe(ready=poe_stash.six_socket_items[:MAX_ITEMS])

def find_chromatic_items(poe_stash):
    MIN_ITEMS = 10
    MAX_ITEMS = 12
    if len(poe_stash.chromatic_items) < MIN_ITEMS:
        return ChromaticRecipe(ready=[])
    return ChromaticRecipe(ready=poe_stash.chromatic_items[:MAX_ITEMS])


def is_recipe_ready(recipe):
    if not recipe:
        return False

    if isinstance(recipe, ChaosRecipe):
        if not recipe.ready_count:
            return False
        return True

    if isinstance(recipe, GemcutterRecipe):
        if not recipe.ready_count:
            return False
        return True

    if isinstance(recipe, SixSocketRecipe):
        return recipe.ready

    if isinstance(recipe, ChromaticRecipe):
        return recipe.ready

    raise RuntimeError('unknown recipe type')

def any_recipes_ready(recipes):
    for recipe in recipes:
        if is_recipe_ready(recipe):
            return True
    return False

def main2(conf):
    exceptions = []
    POESESSID = conf['poesessid']
    url = league_active_rank_url.format(league=LEAGUE, account=ACCOUNT)
    resp = requests.get(url)
    j = resp.json()

    entries = j['entries']

    if len(entries):
        fstentry = entries[0]
        rank = fstentry['rank']
        level = fstentry['character']['level']
        experience = fstentry['character']['experience']

        prev_xp_diff, next_xp_diff = get_prev_next_xp(rank)
        xpdiff_desc = 'rank up xp: -{prev_xp_diff}K rank down xp: +{next_xp_diff}K'.format(prev_xp_diff=prev_xp_diff, next_xp_diff=next_xp_diff)


        time_now = time.time()
        timestr = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())


        measure = (time_now, experience, level)

        for time_measures, max_minutes in time_measures_per_min:
            time_measures.append(measure)

        (xph, hours_remaining) = compute_xph(time_measures_per_min, time_now, level, experience)

        pretty_xp = round(experience/1000000, 2)
        samples = [len(time_measures) for time_measures, _ in time_measures_per_min]
        xph_minutes_desc = 'xph (' +  '/'.join([str(minutes) for _, minutes in time_measures_per_min]) + ' min)'  # eg xph (5/10/15 min)
        print(timestr, 'rank', rank, 'level', level, 'xp', pretty_xp, xph_minutes_desc, xph, 'hours to level', hours_remaining, 'samples', samples)
        print(xpdiff_desc)

        txt_fmt = 'rank: {rank} level: {level} experience: {experience}M {xph_minutes_desc}: {xph} hours to level: {hours_remaining}'
        txt_fmt += '\n' + xpdiff_desc
        txt = txt_fmt.format(rank=rank, level=level, experience=pretty_xp, xph_minutes_desc=xph_minutes_desc, xph=xph, hours_remaining=hours_remaining)
        write_file(txtpath, txt)
    else:
        print('rank unknown')
        write_file(txtpath, 'rank unknown')


    poe_stash = PoeStash(POESESSID)
    chaos_recipe = find_chaos_recipe_needed(poe_stash)
    chaos_recipe_txt = format_chaos_recipe(chaos_recipe, colorize=True)
    print(chaos_recipe_txt)

    gemcutter_recipe = find_gemcutter_needed(poe_stash)
    six_socket_recipe = find_six_sockets(poe_stash)
    chromatic_recipe = find_chromatic_items(poe_stash)
    return chaos_recipe, gemcutter_recipe, six_socket_recipe, chromatic_recipe, poe_stash


def run_once(conf):
    chaos_recipe = None
    if not find_poe():
        raise PoeNotFoundException()
    chaos_recipe, gemcutter_items, six_socket_recipe, chromatic_recipe, poe_stash = main2(conf)
    return chaos_recipe, gemcutter_items, six_socket_recipe, chromatic_recipe, poe_stash


def read_conf():
    with open('secrets.json', 'r') as f:
        conf = json.loads(f.read())
    return conf

def main():
    colorama.init()
    conf = read_conf()
    while True:
        run_once(conf)
        time.sleep(SLEEP_SEC)



