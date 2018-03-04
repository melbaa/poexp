import time
import traceback
import collections

import requests


txtpath = r"C:\users\melba\desktop\desktop\poerank.txt"
account = "emfan"
#league = "Abyss"
league = "Bestiary"

sleep = 10

api_url = "http://api.pathofexile.com/ladders/{league}?accountName={account}"


MAX_QUEUE_LEN = 2000
BASE_TIME_MEASURE_MINUTES = 15
time_measures_per_min = [
    (collections.deque(maxlen=MAX_QUEUE_LEN), 3**0 * BASE_TIME_MEASURE_MINUTES),
    (collections.deque(maxlen=MAX_QUEUE_LEN), 3**1 * BASE_TIME_MEASURE_MINUTES),
    (collections.deque(maxlen=MAX_QUEUE_LEN), 3**2 * BASE_TIME_MEASURE_MINUTES),
]

xp_per_level = {
    93: 2455921256,
    94: 2876116901,
    95: 3111280300,
    96: 3364828162,
    97: 3638186694,
    98: 3932818530,
    99: 4250334444,
}

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


while True:
    try:
        url = api_url.format(league=league, account=account)
        resp = requests.get(url)
        j = resp.json()

        rank = 'n/a'
        level = 'n/a'
        experience = 'n/a'
        hours_remaining = 0
        samples = 0

        entries = j['entries']

        if len(entries):

            rank = entries[0]['rank']
            level = j['character']['level']
            experience = j['character']['experience']

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

            txt_fmt = 'rank: {rank} level: {level} experience: {experience} {xph_minutes_desc}: {xph} hours to level: {hours_remaining}'
            txt = txt_fmt.format(rank=rank, level=level, experience=pretty_xp, xph_minutes_desc=xph_minutes_desc, xph=xph, hours_remaining=hours_remaining)
            write_file(txtpath, txt)
        else:
            print('rank unknown')
            write_file(txtpath, 'rank unknown')


    except Exception as e:
        traceback.print_exc()
        print('exc ignored')



    time.sleep(sleep)
