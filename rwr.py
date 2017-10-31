from memoized_property import memoized_property
from collections import OrderedDict
from geolite2 import geolite2
from lxml import html, etree
from PIL import Image
from glob import glob
import requests
import rwrs
import math
import re
import os

_time_regex = re.compile(r'(?:(?P<h>\d+)h(?:\s+)?)?(?:(?P<m>\d+)m(?:in)?(?:\s+)?)?(?:(?P<s>\d+)s)?')
_rank_image_regex = re.compile(r'rank(?P<rank_id>\d+)')
_map_path_regex = re.compile(r'media/packages/(?P<game_type>.+)/maps/(?P<map_id>.+)$')

_one_minute = 60
_one_hour = _one_minute * 60

MAPS = {
    # Official vanilla maps
    'vanilla': {
        'map1': {'name': 'Moorland Trenches', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Moorland_Trenches'},
        'map1_2': {'name': 'Moorland Trenches (v2)', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Moorland_Trenches'},
        'map2': {'name': 'Keepsake Bay', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Keepsake_Bay'},
        'map3': {'name': 'Old Fort Creek', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Old_Fort_Creek'},
        'map5': {'name': 'Bootleg Islands', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Bootleg_Islands'},
        'map6': {'name': 'Rattlesnake Crescent', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Rattlesnake_Crescent'},
        'map7': {'name': 'Power Junction', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Power_Junction'},
        'map8': {'name': 'Vigil Island', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Vigil_Island'},
        'map9': {'name': 'Black Gold Estuary', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Black_Gold_Estuary'},
        'map10': {'name': 'Railroad Gap', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Railroad_Gap'},
        'map11': {'name': 'Copehill Down', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Copehill_Down'},
        'map13': {'name': 'Iron Enclave', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Iron_Enclave'},
        'map14': {'name': 'Misty Heights', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Misty_Heights'},
        'map15': {'name': 'Islet of Eflen', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Islet_of_Eflen'},
        'pvp1': {'name': 'Islet of Eflen', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Islet_of_Eflen'}
    },

    # Official vanilla maps (winter)
    'vanilla.winter': {
        'map4': {'name': 'Fridge Valley', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Fridge_Valley'},
        'map12': {'name': 'Frozen Canyon', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Frozen_Canyon'}
    },

    # Official Pacific DLC maps
    'pacific': {
        'island1': {'name': 'Guadalcanal', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Guadalcanal'},
        'island2': {'name': 'Russell Islands', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Russell_Islands'},
        'island3': {'name': 'Bougainville Island', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Bougainville_Island'},
        'island4': {'name': 'Tarawa', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Tarawa'},
        'island5': {'name': 'Saipan', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Saipan'},
        'island6': {'name': 'Iwo Jima', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Iwo_Jima'},
        'island7': {'name': 'Operation Downfall', 'has_images': True, 'url': 'https://runningwithrifles.gamepedia.com/Operation_Downfall'}
    },

    # Running with the Dead mod maps
    'Running_with_the_Dead': {
        'rwd_map1': {'name': 'Moorland Trenches (RWD)', 'has_images': False}
    },

    # Overlord Defense mod maps
    'overlord_defense': {
        'def_dday': {'name': 'D-Day (defense)', 'has_images': False}
    }
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
])


SERVER_MODES = {
    'COOP': 'Coop.',
    'DOM': 'Dom.',
    'PvP': 'PvP',
    'PvPvE': 'PvPvE'
}


SERVER_TYPES = {
    'vanilla': 'Vanilla',
    'vanilla.winter': 'Vanilla',
    'pacific': 'Pacific DLC',
    'Running_with_the_Dead': 'Running with the Dead',
    'overlord_defense': 'Overlord Defense',
}


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


def parse_map_path(map_path):
    """Parse a map path to extract the game type it belong to as well as the map identifier."""
    game_type = None
    map_id = None

    parsed = _map_path_regex.search(map_path)

    if parsed:
        parsed = parsed.groupdict()

        game_type = parsed['game_type']
        map_id = parsed['map_id']

    return game_type, map_id


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
        minimaps_paths = glob(os.path.join(self.packages_dir, '*', 'maps', '*', 'map.png'))

        for minimap_path in minimaps_paths:
            game_type, map_id = parse_map_path(minimap_path.replace('\\', '/').replace('/map.png', ''))

            if not map_id or map_id == 'lobby' or game_type == 'teddy_hunt':
                continue

            # Copy the original minimap first
            minimap = Image.open(minimap_path)
            minimap.save(os.path.join(self.output_dir, game_type, map_id + '.png'), optimize=True)

            # Create the thumbnail
            minimap.thumbnail(self.minimap_image_size, Image.ANTIALIAS)
            minimap.save(os.path.join(self.output_dir, game_type, map_id + '_thumb.png'), optimize=True)


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

    def _call(self, endpoint, resource, type, params=None):
        """Perform an HTTP GET request to the desired RWR list endpoint."""
        url = endpoint + resource

        headers = {
            'User-Agent': 'RWRS'
        }

        response = requests.get(url, params=params, headers=headers)

        response.raise_for_status()

        if type == 'html':
            return html.fromstring(response.text)
        elif type == 'xml':
            return etree.fromstring(response.text)
        else:
            raise ValueError('Invalid type parameter')

    @rwrs.cache.memoize(timeout=rwrs.app.config['SERVERS_CACHE_TIMEOUT'])
    def get_servers(self):
        """Get and parse the list of all available public RWR servers."""
        xml_servers = self._call(self.servers_endpoint, 'get_server_list.php', 'xml', params={'start': 0, 'size': 100})
        html_servers = self._call(self.servers_endpoint, 'view_servers.php', 'html')

        servers = []

        for xml_node in xml_servers.xpath('/result/server'):
            servers.append(Server.load(xml_node, html_servers))

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
                'ip_and_port': server.ip_and_port,
                'name': server.name,
                'website': server.website,
                'is_ranked': server.is_ranked,
                'steam_join_link': server.steam_join_link,
                'type': server.type_name,
                'mode': server.mode_name,
                'location': {
                    'country_code': server.location.country_code,
                    'country_name': server.location.country_name
                },
                'map': {
                    'id': server.map.id,
                    'name': server.map.name,
                    'has_images': server.map.has_images,
                    'url': server.map.url,
                },
                'players': {
                    'current': server.players.current,
                    'max': server.players.max,
                    'free': server.players.free,
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

        html_content = self._call(self.players_endpoint, 'view_players.php', 'html', params=params)

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

        html_content = self._call(self.players_endpoint, 'view_player.php', 'html', params=params)

        node = html_content.xpath('(//table/tr[position() = 2])[1]')

        if not node:
            return None

        return Player.load(node[0], alternative=True)

    def __repr__(self):
        return 'rwrs_data_scraper'


class Server:
    website = None

    @classmethod
    def load(cls, xml_node, html_servers):
        """Load a server data from an XML and the HTML code of the servers list page."""
        ret = cls()

        name_node = xml_node.find('name')
        address_node = xml_node.find('address')
        port_node = xml_node.find('port')
        map_id_node = xml_node.find('map_id')
        bots_node = xml_node.find('bots')
        current_players_node = xml_node.find('current_players')
        version_node = xml_node.find('version')
        dedicated_node = xml_node.find('dedicated')
        comment_node = xml_node.find('comment')
        url_node = xml_node.find('url')
        max_players_node = xml_node.find('max_players')
        mode_node = xml_node.find('mode')
        realm_node = xml_node.find('realm')

        ret.name = name_node.text

        ret.ip = address_node.text
        ret.port = int(port_node.text)
        ret.ip_and_port = '{ip}:{port}'.format(ip=ret.ip, port=ret.port)

        game_type, map_id = parse_map_path(map_id_node.text.replace('//', '/'))

        ret.type = game_type

        ret.map = ServerMap()
        ret.map.id = map_id

        if ret.type in MAPS and ret.map.id in MAPS[ret.type]:
            ret.map.name = MAPS[ret.type][ret.map.id]['name']
            ret.map.has_images = MAPS[ret.type][ret.map.id]['has_images']

            if 'url' in MAPS[ret.type][ret.map.id]:
                ret.map.url = MAPS[ret.type][ret.map.id]['url']

        ret.bots = int(bots_node.text)

        ret.players = ServerPlayers()
        ret.players.current = 0 if int(current_players_node.text) < 0 else int(current_players_node.text)
        ret.players.max = int(max_players_node.text)
        ret.players.free = ret.players.max - ret.players.current

        ret.version = version_node.text
        ret.is_dedicated = True if dedicated_node.text == '1' else False
        ret.comment = comment_node.text

        if url_node.text:
            ret.website = url_node.text

        ret.mode = mode_node.text

        ret.is_ranked = realm_node.text == 'official_invasion' # Only server stats with this realm are shared between each other and are available to be viewed

        ret.location = ServerLocation()

        with geolite2 as gl2:
            location = gl2.reader().get(ret.ip)

            if location:
                ret.location.country_code = location['country']['iso_code'].lower()
                ret.location.country_name = location['country']['names']['en']

        ret.steam_join_link = 'steam://rungameid/270150//server_address={ip} server_port={port}'.format(ip=ret.ip, port=ret.port)

        html_server_node = html_servers.xpath('(//table/tr[(td[3] = \'{ip}\') and (td[4] = \'{port}\')])[1]'.format(ip=ret.ip, port=ret.port))

        if html_server_node:
            html_server_node = html_server_node[0]

            players_node = html_server_node[11]

            if players_node.text:
                ret.players.list = [player_name.strip() for player_name in players_node.text.split(',')]
                ret.players.list.sort()

        return ret

    @property
    def mode_name(self):
        return SERVER_MODES[self.mode] if self.mode in SERVER_MODES else 'N/A'

    @property
    def type_name(self):
        return SERVER_TYPES[self.type] if self.type in SERVER_TYPES else 'N/A'

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
        def _init_unlockable(ret, type):
            ret[type] = {
                'list': [],
                'current': 0,
                'max': len([un for required_xp, unlocks in UNLOCKABLES.items() for unlock_id, unlock in unlocks.items() if unlock_id == type for un in unlock])
            }

        def _compute_unlockable(unlocks, ret, type):
            if type in unlocks:
                for unlockable in unlocks[type]:
                    unlocked = self.xp >= required_xp

                    unlockable['required_xp'] = required_xp
                    unlockable['unlocked'] = unlocked

                    if unlocked:
                        ret[type]['current'] += 1

                    ret[type]['list'].append(unlockable)

        ret = {
            'squad_mates': {
                'current': math.floor(self.xp / SQUADMATES_STEPS_XP) if self.xp < MAX_SQUADMATES * SQUADMATES_STEPS_XP else MAX_SQUADMATES,
                'xp_steps': SQUADMATES_STEPS_XP,
                'max': MAX_SQUADMATES
            }
        }

        _init_unlockable(ret, 'radio_calls')
        _init_unlockable(ret, 'weapons')
        _init_unlockable(ret, 'equipment')
        _init_unlockable(ret, 'throwables')

        for required_xp, unlocks in UNLOCKABLES.items():
            _compute_unlockable(unlocks, ret, 'radio_calls')
            _compute_unlockable(unlocks, ret, 'weapons')
            _compute_unlockable(unlocks, ret, 'equipment')
            _compute_unlockable(unlocks, ret, 'throwables')

        return ret

    def __repr__(self):
        return self.username


class ServerMap:
    name = None
    has_images = False
    url = None

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
