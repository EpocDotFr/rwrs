from flask import request
import socket
import struct


__all__ = [
    'humanize_seconds',
    'humanize_integer',
    'ip2long',
    'long2ip',
    'merge_query_string_params'
]


def humanize_seconds(seconds):
    """Return a human-readable representation of the given number of seconds."""
    if not seconds:
        return ''

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
