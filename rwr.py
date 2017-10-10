from memoized_property import memoized_property
from collections import OrderedDict
from geolite2 import geolite2
from PIL import Image
from lxml import html
from glob import glob
import rwrs
import requests
import math
import re
import os

_players_count_regex = re.compile(r'(?P<current_players>\d+)/(?P<max_players>\d+)')
_time_regex = re.compile(r'(?:(?P<h>\d+)h(?:\s+)?)?(?:(?P<m>\d+)m(?:in)?(?:\s+)?)?(?:(?P<s>\d+)s)?')
_rank_image_regex = re.compile(r'rank(?P<rank_id>\d+)')

_one_minute = 60
_one_hour = _one_minute * 60

MAPS = {
    # Official RWR maps
    'map1': {'name': 'Moorland Trenches', 'is_official': True},
    'map1_2': {'name': 'Moorland Trenches', 'is_official': True},
    'map2': {'name': 'Keepsake Bay', 'is_official': True},
    'map3': {'name': 'Old Fort Creek', 'is_official': True},
    'map4': {'name': 'Fridge Valley', 'is_official': True},
    'map5': {'name': 'Bootleg Islands', 'is_official': True},
    'map6': {'name': 'Rattlesnake Crescent', 'is_official': True},
    'map7': {'name': 'Power Junction', 'is_official': True},
    'map8': {'name': 'Vigil Island', 'is_official': True},
    'map9': {'name': 'Black Gold Estuary', 'is_official': True},
    'map10': {'name': 'Railroad Gap', 'is_official': True},
    'map11': {'name': 'Copehill Down', 'is_official': True},
    'map12': {'name': 'Frozen Canyon', 'is_official': True},
    'map13': {'name': 'Iron Enclave', 'is_official': True},
    'map14': {'name': 'Misty Heights', 'is_official': True},
    'map15': {'name': 'Islet of Eflen', 'is_official': True},
    'pvp1': {'name': 'Islet of Eflen', 'is_official': True},

    # Running with the Dead mod maps
    'rwd_map1': {'name': 'Running with the Dead mod', 'is_official': False},

    # Overlord Defense mod maps
    'def_dday': {'name': 'Overlord Defense mod', 'is_official': False}
}

RANKS = {
    0: {'name': 'Private', 'xp': 0},
    1: {'name': 'Private 1st Class', 'xp': 500},
    2: {'name': 'Corporal', 'xp': 1000},
    3: {'name': 'Sergeant', 'xp': 2000},
    4: {'name': 'Staff Sergeant', 'xp': 3000},
    5: {'name': 'Staff Sergeant 1st Class', 'xp': 4000},
    6: {'name': '2nd Lieutenant', 'xp': 6000},
    7: {'name': 'Lieutenant', 'xp': 8000},
    8: {'name': 'Captain', 'xp': 10000},
    9: {'name': 'Major', 'xp': 12000},
    10: {'name': 'Lieutenant Colonel', 'xp': 14000},
    11: {'name': 'Colonel', 'xp': 20000},
    12: {'name': 'Brigadier General', 'xp': 50000},
    13: {'name': 'Major General', 'xp': 100000},
    14: {'name': 'Lieutenant General', 'xp': 200000},
    15: {'name': 'General', 'xp': 500000},
    16: {'name': 'General of the Army', 'xp': 1000000}
}

SQUADMATES_STEPS_XP = 1000 # One squad mate is gained every 1000 XP
MAX_SQUADMATES = 10 # Maximum squad mates allowed

UNLOCKABLES = OrderedDict([
    (0, {
        'weapons': [
            {'image': 'm16a4', 'name': 'Assault rifles'},
            {'image': 'mossberg', 'name': 'Shotguns'}
        ],
        'equipment': [
            {'image': 'riot_shield', 'name': 'Riot shield'}
        ],
        'throwables': [
            {'image': 'grenade', 'name': '2 hand/stun grenades'}
        ]
    }),
    (500, {
        'weapons': [
            {'image': 'm72law', 'name': 'Bazooka'},
            {'image': 'mk23', 'name': 'Silenced pistols'} # TODO Verify
        ],
        'equipment': [
            {'image': 'hesco_barrier', 'name': 'Deployable cover'}
        ],
        'throwables': [
            {'image': 'impact_grenade', 'name': '2 impact grenades'}
        ]
    }),
    (1000, {
        'radio_calls': [
            {'image': 'mortar1', 'name': 'Mortar strike (1x8)'},
            {'image': 'hesco_barrier', 'name': 'Sandbag drop'}
        ],
        'weapons': [
            {'image': 'm60e4', 'name': 'Machineguns'},
            {'image': 'desert_eagle', 'name': 'Desert Eagle pistol'}
        ],
        'throwables': [
            {'image': 'c4', 'name': '1 C4'}
        ]
    }),
    (1500, {
        'weapons': [
            {'image': 'm24a2', 'name': 'Sniper rifles'},
            {'image': 'p90', 'name': 'Advanced assault rifles'}, # TODO Verify
            {'image': 'mp5sd', 'name': 'Silent SMGs'},
            {'image': 'l85a2', 'name': 'L85A2'},
            {'image': 'pepperdust', 'name': 'Pepperdust shotgun'}
        ],
        'throwables': [
            {'image': 'claymore', 'name': '1 Claymore mine'}
        ]
    }),
    (2000, {
        'weapons': [
            {'image': 'm72law', 'name': 'Second bazooka'}
        ],
        'equipment': [
            {'image': 'deployable_mg', 'name': 'Deployable machinegun nest'},
            {'image': 'minigun', 'name': 'Deployable minigun nest'},
            {'image': 'mortar', 'name': 'Deployable mortar'}
        ],
        'throwables': [
            {'image': 'grenade', 'name': '3 hand/stun/impact grenades'},
            {'image': 'c4', 'name': '2 C4'}
        ]
    }),
    (3000, {
        'radio_calls': [
            {'image': 'mortar2', 'name': 'Mortar strike (3x8)'},
            {'image': 'paratroopers1', 'name': '4 paratroops'},
            {'image': 'rubber_boat', 'name': 'Boat drop'},
            {'image': 'buggydrop', 'name': 'Buggy drop'}
        ],
        'weapons': [
            {'image': 'aa-12', 'name': 'AA-12 shotgun'},
            {'image': 'xm8', 'name': 'XM-8 assault rifle'},
            {'image': 'f2000', 'name': 'F2000 rifle'},
            {'image': 'p90', 'name': 'P90 submachinegun'}
        ],
        'throwables': [
            {'image': 'claymore', 'name': '2 Claymore mine'},
            {'image': 'c4', 'name': '3 C4'}
        ]
    }),
    (4000, {
        'radio_calls': [
            {'image': 'artillery1', 'name': 'Artillery strike (2x16)'},
            {'image': 'paratroopers2', 'name': '8 Paratroops'},
            {'image': 'humveedrop', 'name': 'Humvee airdrop'}
        ],
        'weapons': [
            {'image': 'benelli_m4', 'name': 'Benelli M4 shotgun'},
            {'image': 'vss_vintorez', 'name': 'VSS Vintorez sniper rifle'},
            {'image': 'ns2000', 'name': 'Neostead 2000 shotgun'},
            {'image': 'xm25', 'name': 'XM-25 Launcher'},
            {'image': 'barrett_m107', 'name': 'Barrett M-107 sniper rifle'}
        ],
        'throwables': [
            {'image': 'grenade', 'name': '4 hand/stun/impact grenades'},
            {'image': 'flare', 'name': '1 paratroop flare'},
            {'image': 'flare', 'name': '1 checkpoint flare'} # TODO
        ]
    }),
    (5000, {
        'radio_calls': [
            {'image': 'tank', 'name': 'Tank drop'}
        ],
        'equipment': [
            {'image': 'tow2', 'name': 'Deployable TOW missile nest'}
        ]
    }),
    (6000, {
        'throwables': [
            {'image': 'flare', 'name': '2 paratroop flare'},
            {'image': 'claymore', 'name': '3 Claymore mine'},
            {'image': 'flare', 'name': '2 checkpoint flare'} # TODO
        ]
    }),
    (7000, {
        'radio_calls': [
            {'image': 'artillery2', 'name': 'Artillery strike (8x16)'}
        ]
    }),
    (10000, {
        'equipment': [
            {'image': 'tow2', 'name': '2nd deployable TOW missile nest'}
        ]
    })
])

# Official invasion servers
RANKED_SERVERS = (
    # JP
    '45.32.63.85:1234',
    '45.32.63.85:1235',

    # US
    '162.248.88.126:1236',
    '162.248.88.126:1234',
    '199.217.117.133:1234',

    # EU
    '31.186.250.67:1234',
    '31.186.250.67:1235',
    '31.186.250.67:2240',

    # AU
    '103.42.224.189:1234'
)


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


def parse_time(string):
    """Parse a humanly-formatted time string."""
    time = _time_regex.match(string)

    if time:
        time = time.groupdict()

        hours = int(time['h']) if time['h'] else 0
        minutes = int(time['m']) if time['m'] else 0
        seconds = int(time['s']) if time['s'] else 0

        return seconds + minutes * _one_minute + hours * _one_hour

    return None


class MinimapsImageExtractor:
    minimap_image_size = (320, 320)

    def __init__(self, game_dir, output_dir):
        self.game_dir = game_dir
        self.output_dir = output_dir

        if not os.path.isdir(self.game_dir):
            raise FileNotFoundError(self.game_dir + ' does not exists')

        if not os.path.isdir(self.output_dir):
            raise FileNotFoundError(self.output_dir + ' does not exists')

        self.packages_dir = os.path.join(self.game_dir, 'media/packages')

    def extract(self):
        """Actually run the extract process."""
        minimaps_paths = glob(os.path.join(self.packages_dir, '*', 'maps', '*.png'), recursive=True)

        for minimap_path in minimaps_paths:
            map_id = os.path.splitext(os.path.basename(minimap_path))[0]

            if map_id == 'lobby':
                continue

            # Copy the original minimap first
            minimap = Image.open(minimap_path)
            minimap.save(os.path.join(self.output_dir, map_id + '.png'), optimize=True)

            # Create the thumbnail
            minimap.thumbnail(self.minimap_image_size, Image.ANTIALIAS)
            minimap.save(os.path.join(self.output_dir, map_id + '_thumb.png'), optimize=True)


class UnlockablesImagesExtractor:
    def __init__(self, game_dir, output_dir):
        self.game_dir = game_dir
        self.output_dir = output_dir

        if not os.path.isdir(self.game_dir):
            raise FileNotFoundError(self.game_dir + ' does not exists')

        if not os.path.isdir(self.output_dir):
            raise FileNotFoundError(self.output_dir + ' does not exists')

        self.textures_dir = os.path.join(self.game_dir, 'media/packages/vanilla/textures')

    def extract(self):
        """Actually run the extract process."""
        unlockables_to_extract = [un['image'] for required_xp, unlocks in UNLOCKABLES.items() for unlock_id, unlock in unlocks.items() for un in unlock]

        paths = glob(os.path.join(self.textures_dir, 'hud_*.png'))

        for path in paths:
            name = os.path.splitext(os.path.basename(path))[0].replace('hud_', '')

            if name not in unlockables_to_extract:
                continue

            image = Image.open(path)
            image.save(os.path.join(self.output_dir, name + '.png'), optimize=True)


class RanksImageExtractor:
    rank_image_size = (64, 64)

    def __init__(self, game_dir, output_dir):
        self.game_dir = game_dir
        self.output_dir = output_dir

        if not os.path.isdir(self.game_dir):
            raise FileNotFoundError(self.game_dir + ' does not exists')

        if not os.path.isdir(self.output_dir):
            raise FileNotFoundError(self.output_dir + ' does not exists')

        self.textures_dir = os.path.join(self.game_dir, 'media/packages/vanilla/textures')

    def extract(self):
        """Actually run the extract process."""
        ranks_paths = glob(os.path.join(self.textures_dir, 'hud_rank*.png'))

        for rank_path in ranks_paths:
            rank_id = os.path.splitext(os.path.basename(rank_path))[0].replace('hud_rank', '')

            rank_image = Image.open(rank_path)

            # Only get the actual content of the image
            rank_image = rank_image.crop(rank_image.convert('RGBa').getbbox())

            # Resize it to fit in the self.rank_image_size dimension
            rank_image.thumbnail(self.rank_image_size, Image.ANTIALIAS)

            paste_pos = (
                math.floor(self.rank_image_size[0] / 2) - math.floor(rank_image.width / 2),
                math.floor(self.rank_image_size[1] / 2) - math.floor(rank_image.height / 2)
            )

            # Paste it in a new image, centered
            new_rank_image = Image.new('RGBA', self.rank_image_size)
            new_rank_image.paste(rank_image, paste_pos)
            new_rank_image.save(os.path.join(self.output_dir, rank_id + '.png'), optimize=True)


class DataScraper:
    servers_endpoint = 'http://rwr.runningwithrifles.com/rwr_server_list/'
    players_endpoint = 'http://rwr.runningwithrifles.com/rwr_stats/'

    def _call(self, endpoint, resource, params=None):
        """Perform an HTTP GET request to the desired RWR list endpoint."""
        url = endpoint + resource

        headers = {
            'User-Agent': 'RWRS'
        }

        response = requests.get(url, params=params, headers=headers)

        response.raise_for_status()

        return html.fromstring(response.text)

    @rwrs.cache.memoize(timeout=rwrs.app.config['SERVERS_CACHE_TIMEOUT'])
    def get_servers(self):
        """Get and parse the list of all available public RWR servers."""
        html_content = self._call(self.servers_endpoint, 'view_servers.php')

        servers = []

        for node in html_content.xpath('//table/tr[position() > 1]'):
            servers.append(Server.load(node))

        return servers

    def search_server(self, ip, port):
        """Search for a RWR public server."""
        servers = self.get_servers()

        for server in servers:
            if server.ip == ip and server.port == port:
                return server

        return None

    def get_players_on_servers_counts(self):
        """Get the total of players currently playing on the total of non-empty servers."""
        servers = self.get_servers()

        playing_players = sum([server.players.current for server in servers])
        non_empty_servers = sum([1 for server in servers if server.players.current > 0])

        return (playing_players, non_empty_servers)

    def get_all_players(self):
        """Get all the players usernames."""
        servers = self.get_servers()

        ret = []

        for server in servers:
            if not server.players.list:
                continue

            ret.extend(server.players.list)

        return list(set(ret))

    def get_all_players_with_servers(self):
        """Get all the players usernames along the server they are playing on."""
        servers = self.get_servers()

        ret = {}

        for server in servers:
            if not server.players.list:
                continue

            ret[server.ip_and_port] = server.players.list

        return ret

    def get_all_players_with_servers_details(self):
        """Get all the players usernames along details about the servers they are playing on."""
        servers = self.get_servers()

        ret = []

        for server in servers:
            if not server.players.list:
                continue

            ret.append({
                'name': server.name,
                'website': server.website,
                'is_ranked': server.is_ranked,
                'steam_join_link': server.steam_join_link,
                'location': {
                    'country_code': server.location.country_code,
                    'country_name': server.location.country_name
                },
                'players': {
                    'current': server.players.current,
                    'max': server.players.max,
                    'list': server.players.list
                }
            })

        return ret

    @rwrs.cache.memoize(timeout=rwrs.app.config['PLAYERS_CACHE_TIMEOUT'])
    def get_players(self, start=0, sort=PlayersSort.SCORE):
        """Get and parse a list of RWR players."""
        params = {
            'start': start,
            'sort': sort
        }

        html_content = self._call(self.players_endpoint, 'view_players.php', params=params)

        players = []

        for node in html_content.xpath('//table/tr[position() > 1]'):
            players.append(Player.load(node))

        return players

    @rwrs.cache.memoize(timeout=rwrs.app.config['PLAYERS_CACHE_TIMEOUT'])
    def search_player(self, username):
        """Search for a RWR player."""
        username = username.upper()

        params = {
            'search': username
        }

        html_content = self._call(self.players_endpoint, 'view_player.php', params=params)

        node = html_content.xpath('(//table/tr[position() = 2])[1]')

        if not node:
            return None

        return Player.load(node[0], alternative=True)

    def __repr__(self):
        return 'rwrs_data_scraper'


class Server:
    website = None

    @classmethod
    def load(cls, node):
        """Load a server data from an HTML <tr> node."""
        ret = cls()

        name_cell = node[1]
        ip_cell = node[2]
        post_cell = node[3]
        map_cell = node[5]
        players_count_cell = node[6]
        bots_count_cell = node[7]
        version_cell = node[8]
        steam_join_link_cell = node[10]
        players_cell = node[11]
        comment_cell = node[12]

        if (len(name_cell)): # Server name cell has a link
            name_hypertext = name_cell[0]

            ret.website = name_hypertext.get('href')
            ret.name = name_hypertext.text
        else:
            ret.name = name_cell.text

        ret.ip = ip_cell.text
        ret.port = int(post_cell.text)
        ret.ip_and_port = '{ip}:{port}'.format(ip=ret.ip, port=ret.port)

        ret.is_ranked = ret.ip_and_port in RANKED_SERVERS
        ret.location = ServerLocation()

        with geolite2 as gl2:
            location = gl2.reader().get(ret.ip)

            if location:
                ret.location.country_code = location['country']['iso_code'].lower()
                ret.location.country_name = location['country']['names']['en']

        ret.map = ServerMap()

        ret.map.id = map_cell.text

        if ret.map.id in MAPS:
            ret.map.name = MAPS[ret.map.id]['name']
            ret.map.is_official = MAPS[ret.map.id]['is_official']

        ret.players = ServerPlayers()

        players = _players_count_regex.match(players_count_cell.text)

        if players:
            players = players.groupdict()

            ret.players.current = int(players['current_players'])
            ret.players.max = int(players['max_players'])
            ret.players.free = ret.players.max - ret.players.current

        ret.bots = int(bots_count_cell.text)
        ret.version = version_cell.text

        ret.steam_join_link = steam_join_link_cell[0].get('href')

        if players_cell.text:
            ret.players.list = [player_name for player_name in players_cell.text.split(', ')]
            ret.players.list.sort()

        ret.comment = comment_cell.text

        return ret

    def __repr__(self):
        return self.ip_and_port


class Player:
    playing_on_server = None

    @classmethod
    def load(cls, node, alternative=False):
        """Load a player data from an HTML <tr> node."""
        ret = cls()

        username_cell = node[1]
        kills_cell = node[2]
        deaths_cell = node[3]
        score_cell = node[4]
        kd_ratio_cell = node[5]
        time_played_cell = node[6]
        longest_kill_streak_cell = node[8 if alternative else 7]
        targets_destroyed_cell = node[9 if alternative else 8]
        vehicles_destroyed_cell = node[10 if alternative else 9]
        soldiers_healed_cell = node[11 if alternative else 10]
        teamkills_cell = node[7 if alternative else 11]
        distance_moved_cell = node[12]
        shots_fired_cell = node[13]
        throwables_thrown_cell = node[14]
        xp_cell = node[15]
        rank_image_cell = node[17]

        ret.username = username_cell.text
        ret.kills = int(kills_cell.text)
        ret.deaths = int(deaths_cell.text)
        ret.score = int(score_cell.text)
        ret.kd_ratio = float(kd_ratio_cell.text)
        ret.time_played = parse_time(time_played_cell.text)
        ret.longest_kill_streak = int(longest_kill_streak_cell.text)
        ret.targets_destroyed = int(targets_destroyed_cell.text)
        ret.vehicles_destroyed = int(vehicles_destroyed_cell.text)
        ret.soldiers_healed = int(soldiers_healed_cell.text)
        ret.teamkills = int(teamkills_cell.text)
        ret.distance_moved = float(distance_moved_cell.text.replace('km', ''))
        ret.shots_fired = int(shots_fired_cell.text)
        ret.throwables_thrown = int(throwables_thrown_cell.text)
        ret.xp = int(xp_cell.text)

        ret.rank = PlayerRank()

        rank_id = _rank_image_regex.search(rank_image_cell[0].get('src'))

        if rank_id:
            ret.rank.id = int(rank_id.groupdict()['rank_id'])

            if ret.rank.id in RANKS:
                ret.rank.name = RANKS[ret.rank.id]['name']

        return ret

    def set_playing_on_server(self, servers):
        """Determine if this user is playing on one of the given servers."""
        for server in servers:
            if not server.players.list:
                continue

            if self.username in server.players.list:
                self.playing_on_server = server

                return

    @memoized_property
    def next_rank(self):
        """Get the next rank of the player (if applicable)."""
        if self.rank.id is None:
            return None

        if self.rank.id == 16: # Highest rank already reached
            return False

        next_rank_id = self.rank.id + 1

        if next_rank_id not in RANKS:
            return None

        ret = RANKS[next_rank_id]
        ret.update({'id': next_rank_id})

        return ret

    @memoized_property
    def xp_to_next_rank(self):
        """Return the amount of XP the player needs to be promoted to the next rank."""
        if not self.next_rank:
            return None

        return self.next_rank['xp'] - self.xp

    @memoized_property
    def xp_percent_completion_to_next_rank(self):
        """Return the percentage of XP the player obtained for the next rank."""
        if not self.next_rank:
            return None

        return round((self.xp * 100) / self.next_rank['xp'], 2)

    @memoized_property
    def unlocks(self):
        """Compute what the player unlocked (or not)."""
        ret = {
            'radio_calls': [],
            'weapons': [],
            'equipment': [],
            'throwables': [],
            'squad_mates': 0
        }

        for required_xp, unlocks in UNLOCKABLES.items():
            if required_xp > self.xp:
                break

            if 'radio_calls' in unlocks:
                ret['radio_calls'].extend(unlocks['radio_calls'])

        return ret

    def __repr__(self):
        return self.username


class ServerMap:
    name = None
    is_official = False

    def __repr__(self):
        return self.id


class ServerPlayers:
    current = 0
    max = 0
    free = 0
    list = []


class ServerLocation:
    country_code = None
    country_name = None

    def __repr__(self):
        return self.country_code


class PlayerRank:
    id = None
    name = None

    def __repr__(self):
        return self.id
