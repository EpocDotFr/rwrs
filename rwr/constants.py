from collections import OrderedDict
from enum import Enum
from rwrs import app
import helpers


MAPS = helpers.load_json(app.config['MAPS_DATA_FILE'])

VALID_MAPS = list(set([map_id for mps in MAPS.values() for map_id in mps.keys()]))

RANKS = helpers.load_json(app.config['RANKS_DATA_FILE'])

ITEMS = helpers.load_json(app.config['ITEMS_DATA_FILE'])

SERVER_MODES = {
    'COOP': {'short': 'Coop.', 'long': 'Cooperation'},
    'DOM': {'short': 'Dom.', 'long': 'Dominance'},
    'PvP': {'short': 'PvP', 'long': 'PvP'},
    'PvE': {'short': 'PvE', 'long': 'PvE'},
    'PvPvE': {'short': 'PvPvE', 'long': 'PvPvE'}
}

VALID_SERVER_MODES = SERVER_MODES.keys()

SERVER_TYPES = OrderedDict([
    ('vanilla', 'Vanilla'),
    ('vanilla.winter', 'Vanilla'),
    ('pvp', 'Vanilla'),
    ('pacific', 'RWR: PACIFIC'),
    ('man_vs_world_mp', 'Man vs World (MP)'),
    ('Running_with_the_Dead', 'Running with the Dead'),
    ('overlord_defense', 'Overlord Defense'),
    ('lab_defense', 'Lab Defense'),
    ('lab_def_koth', 'Lab Defense KOTH'),
    ('viper', 'Viper')
])

VALID_SERVER_TYPES = SERVER_TYPES.keys()

PLAYERS_LIST_DATABASES = OrderedDict([
    ('invasion', {'name': 'Invasion', 'ranks_country': 'us', 'realm': 'official_invasion'}),
    ('pacific', {'name': 'Pacific', 'ranks_country': app.config['PACIFIC_PLAYERS_RANKS_COUNTRY'], 'realm': 'official_pacific'})
])

VALID_DATABASES = PLAYERS_LIST_DATABASES.keys()
VALID_DATABASES_STRING_LIST = ','.join(VALID_DATABASES)


class PlayersSort(Enum):
    USERNAME = 'username'
    KILLS = 'kills'
    DEATHS = 'deaths'
    SCORE = 'score'
    KD_RATIO = 'kd'
    TIME_PLAYED = 'time_played'
    LONGEST_KILL_STREAK = 'longest_kill_streak'
    TARGETS_DESTROYED = 'targets_destroyed'
    VEHICLES_DESTROYED = 'vehicles_destroyed'
    SOLDIERS_HEALED = 'soldiers_healed'
    TEAMKILLS = 'teamkills'
    DISTANCE_MOVED = 'distance_moved'
    SHOTS_FIRED = 'shots_fired'
    THROWABLES_THROWN = 'throwables_thrown'
    XP = 'rank_progression'

VALID_PLAYERS_SORTS = [ps.value for ps in PlayersSort]

CONTINENTS = OrderedDict([
    ('af', 'Africa'),
    ('na', 'North America'),
    ('oc', 'Oceania'),
    ('an', 'Antarctica'),
    ('as', 'Asia'),
    ('eu', 'Europe'),
    ('sa', 'South America'),
])

VALID_CONTINENTS = CONTINENTS.keys()
