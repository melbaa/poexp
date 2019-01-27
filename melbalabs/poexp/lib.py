import time
import traceback
import collections
import json

import requests
import colorama
import win32api
import win32gui

txtpath = r"C:\users\melba\desktop\desktop\poerank.txt"
ACCOUNT = "emfan"
#LEAGUE = "Abyss"
#LEAGUE = "Bestiary"
#LEAGUE = "Incursion"
#LEAGUE = "Delve"
LEAGUE = "Betrayal"

SLEEP_SEC = 15  # sec

api_url = "http://api.pathofexile.com/ladders/{league}?accountName={account}"
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

ChaosRecipe = collections.namedtuple('ChaosRecipe', ['need', 'unknown', 'identified', 'counts'])

class LoginException(RuntimeError):
    pass

class PoeNotFoundException(RuntimeError):
    pass

class PoeStash:
    def __init__(self, poesessid):
        # note first tab in inventory
        url = stash_url.format(league=LEAGUE, account=ACCOUNT, tabindex=0, tabs=0)
        resp = requests.get(url, cookies={'POESESSID': poesessid})
        j = resp.json()
        if 'error' in j:
            raise LoginException(j['error']['message'])
        self.raw = j
        self.items = j['items']

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

def find_chaos_recipe_needed(stash):
    HOWMANY = 5
    counts = {
            'helmet': 0,
            'boots': 0,
            'gloves': 0,
            'ring': 0,
            'amulet': 0,
            'belt': 0,
            'weapons': 0,
            'chest': 0,
    }
    unknown = []
    identified = []
    items = stash.items
    for item in items:
        if item['identified']:
            identified.append(item['typeLine'])
            continue
        category = list(item['category'].keys())[0]
        if category == 'weapons':
            counts['weapons'] += 1
        elif category in {'accessories', 'armour'}:
            item_class = item['category'][category][0]
            counts[item_class] += 1
        else:
            unknown.append(item)

    need = []
    for name, count in counts.items():
        if name == 'ring' and count < HOWMANY * 2:
            need.append(name)
        elif count < HOWMANY:
            need.append(name)

    return ChaosRecipe(need, unknown, identified, counts)

def color_chaos_recipe(chaos_recipe):
    # broken with powershell, works with default terminal or conemu
    # not enough colors
    f = colorama.Fore
    b = colorama.Back
    s = colorama.Style
    colors = {
        'helmet': f.BLUE,
        'boots': f.CYAN,
        'gloves': f.YELLOW,
        'ring': f.MAGENTA,
        'amulet': f.GREEN,
        'belt': f.GREEN,
        'weapons': f.RED,
        'chest': f.RED,
    }
    need, unknown, identified, counts = chaos_recipe
    need_color = []
    for item in need:
        if item in colors:
            item = colors[item] + item + s.RESET_ALL
        need_color.append(item)
    chaos_recipe_cli_txt = 'need:{}, unk:{}, id:{} | r:{} a:{} b:{} | h:{} b:{} g:{} w:{} c:{}'.format(
            ', '.join(need_color),
            unknown,
            identified,
            counts['ring'],
            counts['amulet'],
            counts['belt'],
            counts['helmet'],
            counts['boots'],
            counts['gloves'],
            counts['weapons'],
            counts['chest'],
    )
    return chaos_recipe_cli_txt


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




def main2(conf):
    exceptions = []
    chaos_recipe = None
    POESESSID = conf['poesessid']
    url = api_url.format(league=LEAGUE, account=ACCOUNT)
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


    stash = PoeStash(POESESSID)
    chaos_recipe = find_chaos_recipe_needed(stash)
    chaos_recipe_txt = color_chaos_recipe(chaos_recipe)
    print(chaos_recipe_txt)

    return chaos_recipe

def run_once(conf):
    chaos_recipe = None
    if find_poe():
        chaos_recipe = main2(conf)
    else:
        raise PoeNotFoundException()
    return chaos_recipe


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



