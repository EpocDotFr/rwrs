from . import constants
import re


_time_regex = re.compile(r'(?:(?P<h>\d+)h(?:\s+)?)?(?:(?P<m>\d+)m(?:in)?(?:\s+)?)?(?:(?P<s>\d+)s)?')
_map_path_regex = re.compile(r'/(?P<server_type>.[^/]+)/maps/(?P<map_id>.+)$')


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


def get_maps(**filters):
    """Return a flattened list of maps, optionally filtered."""
    def _filter_map(map, filters):
        if filters.get('has_minimap') is not None and filters.get('has_minimap') != map['has_minimap']:
            return False

        return True

    ret = []

    for server_type, maps in constants.MAPS.items():
        for map_id, map in maps.items():
            if _filter_map(map, filters):
                map['id'] = map_id
                map['server_type'] = server_type

                ret.append(map)

    return ret


def get_map(server_type, map_id):
    """Get a single map."""
    if server_type not in constants.MAPS or map_id not in constants.MAPS[server_type]:
        return None

    map = constants.MAPS[server_type][map_id]

    map['id'] = map_id
    map['server_type'] = server_type

    return map
