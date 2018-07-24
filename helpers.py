from collections import OrderedDict
from flask import request
from rwrs import app
import subprocess
import platform
import json
import os


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


def ping(host, network_timeout=3):
    """Send a ping packet to the specified host, using the system "ping" command."""
    args = [
        'ping'
    ]

    platform_os = platform.system()

    if platform_os == 'Windows':
        args.extend(['-n', '1'])
        args.extend(['-w', str(network_timeout * 1000)])
    elif platform_os in ('Linux', 'Darwin'):
        args.extend(['-c', '1'])
        args.extend(['-W', str(network_timeout)])
    else:
        raise NotImplemented('Unsupported OS: {}'.format(platform_os))

    args.append(host)

    try:
        if platform_os == 'Windows':
            output = subprocess.run(args, check=True, universal_newlines=True).stdout

            if output and 'TTL' not in output:
                return False
        else:
            subprocess.run(args, check=True)

        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


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
