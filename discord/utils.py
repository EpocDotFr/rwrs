from flask_discord_interactions import Message
from functools import wraps
from . import constants
from flask import g
import arrow
import re

_time_ago_regex = re.compile(r'(?P<days_ago>\d+) day(?:s?) ago|(?P<weeks_ago>\d+) week(?:s?) ago|(?P<months_ago>\d+) month(?:s?) ago|(?P<years_ago>\d+) year(?:s?) ago')


def prepare_username(username):
    """Perform some action to a RWR username to be ready to be consumed by the bot."""
    username = username.upper()

    if not username.startswith('\-'):
        return username

    return username.replace('\-', '-', 1)


def parse_date(date):
    """Parse a user-friendly date and return an arrow instance."""
    now = arrow.utcnow().floor('day')

    if date == 'yesterday':
        return now.shift(days=-1)

    time_ago_match = _time_ago_regex.match(date)

    if time_ago_match:
        time_ago = time_ago_match.groupdict()

        if time_ago['days_ago']:
            return now.shift(days=-int(time_ago['days_ago']))

        if time_ago['weeks_ago']:
            return now.shift(weeks=-int(time_ago['weeks_ago']))

        if time_ago['months_ago']:
            return now.shift(months=-int(time_ago['months_ago']))

        if time_ago['years_ago']:
            return now.shift(years=-int(time_ago['years_ago']))

    allowed_formats = [
        'MMM D YYYY',
        'MMM DD YYYY',
        'MMM D, YYYY',
        'MMM DD, YYYY',
        'MMM D',
        'MMM DD',
        'MMMM D YYYY',
        'MMMM DD YYYY',
        'MMMM D, YYYY',
        'MMMM DD, YYYY',
        'MMMM D',
        'MMMM DD',
        'DD/MM/YYYY',
        'D/M/YYYY',
        'YYYY-M-D',
        'YYYY-MM-DD'
    ]

    ret = arrow.get(date, allowed_formats)

    if ret.year == 1:
        ret = ret.replace(year=now.year)

    return ret


def compare_values(source_player, target_player, getter):
    """Create the comparison cell for the compare command."""
    source_value = getter(source_player)
    target_value = getter(target_player)

    def _compare(source_value, target_value):
        if source_value > target_value:
            return '▲'
        elif source_value < target_value:
            return '▼'
        else:
            return '='

    return _compare(source_value, target_value) + '  ' + _compare(target_value, source_value)


def permissions(names):
    return [permission for name, permission in constants.PERMISSIONS.items() if name in names]


def admin_permissions():
    return permissions([
        'myself',
    ])


def event_manager_permissions():
    return admin_permissions() + permissions([
        'jackmayol',
    ])


def has_permissions(user, permissions):
    for permission in permissions:
        if ((permission.type == 1 and permission.id in user.roles) or (permission.type == 2 and permission.id == user.id)) and permission.permission:
            return True

    return False


def check_maintenance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args:
            ctx = args[0]

            if g.UNDER_MAINTENANCE and not has_permissions(ctx.author, admin_permissions()):
                return Message(':wrench: RWRS is under ongoing maintenance! Please try again later.', ephemeral=True)

        return func(*args, **kwargs)

    return wrapper
