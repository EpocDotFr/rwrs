from collections import OrderedDict
from flask import request
import subprocess
import platform
import socket
import struct
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


def ip2long(ip):
    """Convert an IP to its integer representation."""
    return struct.unpack('!L', socket.inet_aton(ip))[0]


def long2ip(long):
    """Convert an integer IP to its string representation."""
    return socket.inet_ntoa(struct.pack('!L', long))


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


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]
