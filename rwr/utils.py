from rwr.player import PlayerRank
from flask import current_app
from rwr import constants
from app import app
import re


_time_regex = re.compile(r'(?:(?P<h>\d+)h(?:\s+)?)?(?:(?P<m>\d+)m(?:in)?(?:\s+)?)?(?:(?P<s>\d+)s)?')
_map_path_regex = re.compile(r'[/\\](?P<server_type>.[^/]+)[/\\]maps[/\\](?P<map_id>.+)$')


def get_mode_name(mode, short=True):
    """Return the server's game mode name."""
    return constants.SERVER_MODES[mode]['short' if short else 'long'] if mode in constants.SERVER_MODES else mode if mode is not None else 'N/A'


def get_type_name(type):
    """Return the server's game type name."""
    return constants.SERVER_TYPES[type] if type in constants.SERVER_TYPES else type if type is not None else 'N/A'


def get_database_name(database):
    """Return the name of a stats database."""
    return constants.PLAYERS_LIST_DATABASES[database]['name'] if database in constants.PLAYERS_LIST_DATABASES else None


def parse_time(string):
    """Parse a humanly-formatted time string."""
    time = _time_regex.match(string)

    if time:
        time = time.groupdict()
        one_minute = 60
        one_hour = one_minute * 60

        hours = int(time['h']) if time['h'] else 0
        minutes = int(time['m']) if time['m'] else 0
        seconds = int(time['s']) if time['s'] else 0

        return seconds + minutes * one_minute + hours * one_hour

    return None


def parse_map_path(map_path):
    """Parse a map path to extract the game type it belong to as well as the map identifier."""
    server_type = None
    map_id = None

    parsed = _map_path_regex.search(map_path)

    if parsed:
        parsed = parsed.groupdict()

        server_type = parsed['server_type']
        map_id = parsed['map_id']

    return server_type, map_id


def get_rank_from_xp(database, xp):
    current_rank_id = None

    for rank_id, rank in constants.RANKS[database].items():
        if rank['xp'] > xp:
            break

        current_rank_id = rank_id

    return get_rank_object(database, int(current_rank_id))


def get_rank_object(database, rank_id):
    """Return a new PlayerRank object given a rank ID."""
    ret = PlayerRank()

    ranks = constants.RANKS[database]

    if str(rank_id) not in ranks:
        return ret

    ret.id = rank_id
    ret.name = ranks[str(rank_id)]['name']
    ret.xp = ranks[str(rank_id)]['xp']

    if current_app:
        ret.set_images_and_icons()
    else:
        with app.app_context():
            ret.set_images_and_icons()

    return ret
