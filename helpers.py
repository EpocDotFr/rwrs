from flask import request, Markup, url_for
from itertools import tee, islice, chain
from collections import OrderedDict
from rwrs import app
import misaka
import json


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
    if app.config['DEBUG']:
        return 'sqlite:///db.sqlite'

    uri = 'mysql+mysqldb://{username}:{password}@'

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


def is_player_myself(player_nickname):
    return player_nickname.lower() == app.config['MY_USERNAME']


def is_player_contributor(player_nickname):
    return player_nickname.lower() in app.config['CONTRIBUTORS']


def is_player_rwr_dev(player_nickname):
    return player_nickname.lower() in app.config['DEVS']


def is_player_ranked_server_mod(player_nickname):
    return player_nickname.lower() in app.config['RANKED_SERVERS_MODS']


def markdown_to_html_inline(markdown):
    html = misaka.html(markdown, extensions=('strikethrough', 'underline'), render_flags=('escape',))
    html = html.replace('<p>', '').replace('</p>', '').strip()

    return Markup(html)


def check_safe_root(url):
    """Return the given URL if it looks OK to redirect to."""
    if url is None:
        return None

    if url.startswith((request.url_root, '/')):
        return url

    return None


def get_next_url():
    """Get the URL to redirect the user to."""
    return check_safe_root(request.args.get('next')) or check_safe_root(request.referrer) or url_for('home')


def generate_next_url():
    """Return the full path of the current URL, minus the ending question mark."""
    return request.full_path.rstrip('?')
