from collections import OrderedDict
from rwrs import app
import helpers


MAPS = helpers.load_json(app.config['MAPS_DATA_FILE'])
RANKS = helpers.load_json(app.config['RANKS_DATA_FILE'])

SQUADMATES_STEPS_XP = 1000 # One squad mate is gained every 1000 XP
MAX_SQUADMATES = 10 # Maximum squad mates allowed

UNLOCKABLES = {
    'vanilla': OrderedDict([
        (0, {
            'weapons': [
                {'image': 'assault_rifles', 'name': 'Assault rifles'},
                {'image': 'shotguns', 'name': 'Shotguns'}
            ],
            'equipment': [
                {'image': 'riot_shield', 'name': 'Riot shield'}
            ],
            'throwables': [
                {'image': 'hand_stun_grenades', 'name': '2 hand/stun grenades'}
            ]
        }),
        (500, {
            'weapons': [
                {'image': 'bazooka', 'name': 'Bazooka'},
                {'image': 'pistols_sd', 'name': 'Silenced pistols'}
            ],
            'equipment': [
                {'image': 'cover', 'name': 'Deployable cover'}
            ],
            'throwables': [
                {'image': 'impact_grenade', 'name': '2 impact grenades'}
            ]
        }),
        (1000, {
            'radio_calls': [
                {'image': 'mortar_1', 'name': 'Mortar strike 1x8'},
                {'image': 'sandbag_drop', 'name': 'Sandbag drop'}
            ],
            'weapons': [
                {'image': 'machineguns', 'name': 'Machineguns'},
                {'image': 'desert_eagle', 'name': 'Desert Eagle pistol'}
            ],
            'throwables': [
                {'image': 'c4', 'name': '1 C4'}
            ]
        }),
        (1500, {
            'weapons': [
                {'image': 'snipers', 'name': 'Sniper rifles'},
                {'image': 'adv_assault_rifles', 'name': 'Advanced assault rifles'},
                {'image': 'smgs_sd', 'name': 'Silent SMGs'},
                {'image': 'l85a2', 'name': 'L85A2'},
                {'image': 'pepperdust', 'name': 'Pepperdust shotgun'}
            ],
            'throwables': [
                {'image': 'claymore', 'name': '1 Claymore mine'}
            ]
        }),
        (2000, {
            'weapons': [
                {'image': 'bazooka', 'name': 'Second bazooka'}
            ],
            'equipment': [
                {'image': 'deployable_mg', 'name': 'Deployable machinegun'},
                {'image': 'deployable_minigun', 'name': 'Deployable minigun'},
                {'image': 'deployable_mortar', 'name': 'Deployable mortar'}
            ],
            'throwables': [
                {'image': 'hand_stun_impact_grenades', 'name': '3 hand/stun/impact grenades'},
                {'image': 'c4', 'name': '2 C4'}
            ]
        }),
        (3000, {
            'radio_calls': [
                {'image': 'mortar_2', 'name': 'Mortar strike 3x8'},
                {'image': 'paratroopers_1', 'name': '4 paratroopers'},
                {'image': 'rubber_boat_drop', 'name': 'Boat drop'},
                {'image': 'buggy_drop', 'name': 'Buggy drop'}
            ],
            'weapons': [
                {'image': 'aa-12', 'name': 'AA-12 shotgun'},
                {'image': 'xm8', 'name': 'XM-8 assault rifle'},
                {'image': 'f2000', 'name': 'F2000 assault rifle'},
                {'image': 'p90', 'name': 'P90 submachinegun'}
            ],
            'throwables': [
                {'image': 'claymore', 'name': '2 Claymore mines'},
                {'image': 'c4', 'name': '3 C4'}
            ]
        }),
        (4000, {
            'radio_calls': [
                {'image': 'artillery_1', 'name': 'Artillery strike 2x16'},
                {'image': 'paratroopers_2', 'name': '8 paratroopers'},
                {'image': 'humvee_drop', 'name': 'Humvee drop'}
            ],
            'weapons': [
                {'image': 'benelli_m4', 'name': 'Benelli M4 shotgun'},
                {'image': 'vss_vintorez', 'name': 'VSS Vintorez sniper rifle'},
                {'image': 'ns2000', 'name': 'Neostead 2000 shotgun'},
                {'image': 'xm25', 'name': 'XM-25 launcher'},
                {'image': 'barrett_m107', 'name': 'Barrett M-107 sniper rifle'}
            ],
            'throwables': [
                {'image': 'hand_stun_impact_grenades', 'name': '4 hand/stun/impact grenades'},
                {'image': 'flare', 'name': '1 paratroopers flare'}
            ]
        }),
        (5000, {
            'radio_calls': [
                {'image': 'tank_drop', 'name': 'Tank drop'}
            ],
            'equipment': [
                {'image': 'deployable_tow', 'name': 'Deployable TOW missile nest'}
            ]
        }),
        (6000, {
            'throwables': [
                {'image': 'flare', 'name': '2 paratroopers flares'},
                {'image': 'claymore', 'name': '3 Claymore mines'}
            ]
        }),
        (7000, {
            'radio_calls': [
                {'image': 'artillery_2', 'name': 'Artillery strike 8x16'}
            ]
        }),
        (10000, {
            'equipment': [
                {'image': 'deployable_tow', 'name': '2nd deployable TOW missile nest'}
            ]
        })
    ]),
    'pacific': OrderedDict([
        (0, {
            'weapons': [

            ],
            'equipment': [

            ]
        }),
        (250, {
            'weapons': [

            ],
            'equipment': [

            ],
            'throwables': [
                {'image': '', 'name': '2 Satchel charges'}, # TODO
                {'image': '', 'name': '2 Type 99 magnetic AT'} # TODO
            ]
        }),
        (500, {
            'weapons': [

            ],
            'equipment': [

            ]
        }),
        (1000, {
            'radio_calls': [
                {'image': 'mortar_1', 'name': 'Mortar strike (light)'}
            ],
            'weapons': [

            ],
            'equipment': [

            ],
            'throwables': [
                {'image': '', 'name': '1 Demolition charges'} # TODO
            ]
        }),
        (1500, {
            'radio_calls': [
                {'image': 'rifle_squad', 'name': 'USMC rifle squad'},
                {'image': 'banzai_charge', 'name': 'Banzai Charge'}
            ],
            'weapons': [

            ],
            'equipment': [

            ]
        }),
        (2000, {
            'radio_calls': [
                {'image': 'mortar_2', 'name': 'Mortar strike (heavy, rockets)'},
                {'image': 'airstrike_1', 'name': 'Airstrike (rockets)'}
            ],
            'weapons': [

            ],
            'equipment': [

            ],
            'throwables': [
                {'image': '', 'name': '2 Demolition charges'}, # TODO
                {'image': '', 'name': '3 MkII grenades'}, # TODO
                {'image': '', 'name': '3 Satchel charges'}, # TODO
                {'image': '', 'name': '3 Type 99 magnetic AT'}, # TODO
                {'image': '', 'name': '4 Type 97 grenades'} # TODO
            ]
        }),
        (3000, {
            'radio_calls': [
                {'image': 'airstrike_2', 'name': 'Airstrike (precision bombing)'},
                {'image': 'rubber_boat_drop', 'name': 'Boat drop'},
                {'image': 'lvt_4', 'name': 'LVT-4'},
                {'image': 'type_1', 'name': 'Type 1 Ho-Ha'}
            ],
            'weapons': [

            ],
            'equipment': [

            ],
            'throwables': [
                {'image': '', 'name': '2 Demolition charges'} # TODO
            ]
        }),
        (4000, {
            'radio_calls': [
                {'image': 'm3', 'name': 'M3 Stuart'},
                {'image': 'type_95', 'name': 'Type 95 Ha-Go'},
                {'image': 'naval_guns_1', 'name': 'Naval Guns (light, saturation)'}
            ],
            'weapons': [

            ],
            'equipment': [

            ],
            'throwables': [
                {'image': '', 'name': '4 MkII grenades'}, # TODO
                {'image': '', 'name': '4 Satchel charges'}, # TODO
                {'image': '', 'name': '5 Type 97 grenades'}, # TODO
                {'image': '', 'name': '4 Type 99 magnetic AT'} # TODO
            ]
        }),
        (5000, {
            'radio_calls': [

            ],
            'weapons': [

            ],
            'equipment': [

            ]
        }),
        (6000, {
            'radio_calls': [

            ],
            'weapons': [

            ],
            'equipment': [

            ]
        }),
        (7000, {
            'weapons': [

            ],
            'equipment': [

            ]
        }),
        (8000, {
            'radio_calls': [
                {'image': 'naval_guns_2', 'name': 'Naval Guns (heavy)'}
            ],
            'weapons': [

            ],
            'equipment': [

            ]
        }),
        (10000, {
            'radio_calls': [

            ],
            'weapons': [

            ],
            'equipment': [

            ]
        })
    ])
}

SERVER_MODES = {
    'COOP': {'short': 'Coop.', 'long': 'Cooperation'},
    'DOM': {'short': 'Dom.', 'long': 'Dominance'},
    'PvP': {'short': 'PvP', 'long': 'PvP'},
    'PvE': {'short': 'PvE', 'long': 'PvE'},
    'PvPvE': {'short': 'PvPvE', 'long': 'PvPvE'}
}

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

PLAYERS_LIST_DATABASES = {
    'invasion': {'name': 'Invasion', 'ranks_country': 'us', 'realm': 'official_invasion'},
    'pacific': {'name': 'Pacific', 'ranks_country': app.config['PACIFIC_PLAYERS_RANKS_COUNTRY'], 'realm': 'official_pacific'}
}

VALID_DATABASES = PLAYERS_LIST_DATABASES.keys()

ROOT_RWR_SERVERS = [
    {
        'label': 'Master servers',
        'description': 'Needed to play online with other people.',
        'servers': [
            {
                'location': 'St Louis, United States',
                'host': 'us3.runningwithrifles.com'
            },
            {
                'location': 'Tokyo, Japan',
                'host': 'jp1.runningwithrifles.com'
            }
        ]
    },
    {
        'label': 'Stats servers',
        'description': 'Needed to keep track of your stats on ranked (official) servers.',
        'servers': [
            {
                'location': 'Chicago, United States',
                'host': 'us6.runningwithrifles.com'
            }
        ]
    }
]


class PlayersSort:
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
