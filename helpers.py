from itertools import tee, islice, chain
from collections import OrderedDict
from flask import request
from rwrs import app
import json
import os
import re

_steam_identity_url_regex = re.compile('steamcommunity.com/openid/id/([0-9]+)$')


def humanize_seconds_to_days(seconds):
    """Return a human-readable representation of the given number of seconds to days / hours / minutes / seconds."""
    if not seconds:
        return '0m'

    d = int(seconds / (60 * 60 * 24))
    h = int((seconds % (60 * 60 * 24)) / (60 * 60))
    m = int((seconds % (60 * 60)) / 60)
    s = int(seconds % 60)

    ret = []

    if d:
        ret.append(('{}d', d))

    if h:
        ret.append(('{}h', h))

    if m:
        ret.append(('{:>02}m', m))

    if s:
        ret.append(('{:>02}s', s))

    f, v = zip(*ret)

    return ' '.join(f).format(*v)


def humanize_seconds_to_hours(seconds):
    """Return a human-readable representation of the given number of seconds to hours / minutes."""
    if not seconds:
        return '0m'

    h = int(seconds / (60 * 60))
    m = int((seconds % (60 * 60)) / 60)

    ret = []

    if h:
        ret.append(('{}h', h))

    if m:
        ret.append(('{:>02}m', m))

    f, v = zip(*ret)

    return ' '.join(f).format(*v)


def humanize_integer(integer):
    """Return a slightly more human-readable representation of the given integer."""
    if not integer:
        return '0'

    return format(integer, ',d').replace(',', ' ')


def merge_query_string_params(params):
    """Return the dict of all the current request query string parameters after merging params in it."""
    args = request.args.to_dict()

    args.update(params)

    return args


def load_json(file):
    """Load a JSON file."""
    if not os.path.isfile(file):
        raise FileNotFoundError('The {} file does not exists'.format(file))

    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f, object_pairs_hook=OrderedDict)


def save_json(file, data):
    """Save data to a JSON file."""
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    return data


def simplified_integer(integer):
    """Return a simplified human-readable integer."""
    if not integer:
        return '0'

    integer = float('{:.3g}'.format(integer))
    magnitude = 0

    while abs(integer) >= 1000:
        magnitude += 1
        integer /= 1000.0

    return '{}{}'.format('{:f}'.format(integer).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def build_database_uri():
    """Return the database connection string."""
    uri = 'mysql+pymysql://{username}:{password}@'

    params = {
        'username': app.config['DB_USERNAME'],
        'password': app.config['DB_PASSWORD']
    }

    if not app.config['DB_UNIX_SOCKET']:
        uri += '{host}:{port}'

        params.update({
            'host': app.config['DB_HOST'],
            'port': app.config['DB_PORT']
        })

    uri += '/{dbname}'

    params.update({
        'dbname': app.config['DB_NAME']
    })

    if app.config['DB_UNIX_SOCKET']:
        uri += '?unix_socket={unix_socket}'

        params.update({
            'unix_socket': app.config['DB_UNIX_SOCKET']
        })

    return uri.format(**params)


def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])

    return zip(prevs, items, nexts)


def parse_steam_id_from_identity_url(identity_url):
    """Extract the Steam ID from a Steam identity URL."""
    match = _steam_identity_url_regex.search(identity_url)

    if match:
        return match.group(1)

    return None


def is_player_myself(player_nickname):
    return player_nickname.lower() == app.config['MY_USERNAME']


def is_player_contributor(player_nickname):
    return player_nickname.lower() in app.config['CONTRIBUTORS']


def is_player_rwr_dev(player_nickname):
    return player_nickname.lower() in app.config['DEVS']


def is_player_ranked_server_admin(player_nickname):
    return player_nickname.lower() in app.config['RANKED_SERVERS_ADMINS']


def get_market_ad_type_name(market_ad_type):
    if market_ad_type == 'offers':
        return 'Offers'
    elif market_ad_type == 'requests':
        return 'Requests'
    else:
        return 'Unknown'

