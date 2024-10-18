from steam.steamid import SteamID
from rwrs.models import Variable
from flask import current_app
from rwr.server import Server
from rwr.player import Player
from lxml import html, etree
from app import app, cache
from rwr import constants
import geoip2.database
import geoip2.errors
import requests

requests = requests.Session()

if app.config['SCRAPER_PROXY']:
    requests.proxies.update({
        'http': app.config['SCRAPER_PROXY'],
    })

servers_base_url = 'http://rwr.runningwithrifles.com/rwr_server_list/'
players_base_url = 'http://rwr.runningwithrifles.com/rwr_stats/'


def _call(url, parser=None, params=None, auth=None, verify=True):
    """Perform an HTTP GET request to the desired RWR list base_url."""
    headers = {
        'User-Agent': 'rwrstats.com'
    }

    response = requests.get(
        url,
        params=params,
        auth=auth,
        headers=headers,
        verify=verify,
        timeout=5
    )

    response.raise_for_status()

    if parser == 'html':
        return html.fromstring(response.text)
    elif parser == 'xml':
        return etree.fromstring(response.text)


def _set_servers_location(servers):
    """Set the location of a list of servers."""
    if not servers:
        return

    geoip_db_reader = geoip2.database.Reader(app.config['GEOIP_DATABASE_FILE'])

    for server in servers:
        try:
            location = geoip_db_reader.city(server.ip)
        except (ValueError, geoip2.errors.AddressNotFoundError):
            continue

        if location:
            if location.continent.geoname_id:
                server.location.continent_code = location.continent.code.lower()
                server.location.continent_name = location.continent.names['en']

            if location.country.geoname_id:
                server.location.country_code = location.country.iso_code.lower()
                server.location.country_name = location.country.names['en']

            if location.city.geoname_id:
                server.location.city_name = location.city.names['en']

            server.location.text = '{}{}'.format(
                server.location.city_name + ', ' if server.location.city_name else '',
                server.location.country_name
            )

            if current_app:
                server.location.set_flags()
            else:
                with app.app_context():
                    server.location.set_flags()

    geoip_db_reader.close()


def _get_list(value_attribute, label_attribute):
    """Return a list of value -> label of the specified servers attributes."""
    servers = get_servers()
    ret = []
    already_handled = []

    for server in servers:
        value = value_attribute(server)
        label = label_attribute(server)

        if value and value not in already_handled:
            ret.append({
                'value': value,
                'label': label
            })

            already_handled.append(value)

    return sorted(ret, key=lambda k: k['label'])


def _set_server_event(servers):
    """Assign the next RWR event to the corresponding server, if applicable."""
    if not servers:
        return

    event = Variable.get_event(with_server=False)

    for server in servers:
        server.event = event if event and event['server_ip_and_port'] and event['server_ip_and_port'] == server.ip_and_port else None


@cache.memoize(timeout=app.config['SERVERS_CACHE_TIMEOUT'])
def get_servers():
    """Get and parse the list of all public RWR servers."""
    all_servers = []
    start = 0
    size = 100

    while True:
        params = {
            'start': start,
            'size': size,
            'names': 1,
            'cdata': 1
        }

        xml_content = _call(
            servers_base_url + 'get_server_list.php',
            parser='xml',
            params=params
        )

        servers = [Server.load(server_node) for server_node in xml_content.xpath('/result/server')]

        if not servers:
            break

        all_servers.extend(servers)

        if servers[-1].is_last:
            break

        start += size

    _set_servers_location(all_servers)
    _set_server_event(all_servers)

    all_servers.sort(
        key=lambda s: s.players.current,
        reverse=True
    )

    return all_servers


def get_server_by_ip_and_port(*args):
    """Search for a RWR public server based on its IP and port."""
    if len(args) == 1:
        def server_found(*args):
            server, ip_and_port = args

            return server.ip_and_port == ip_and_port
    elif len(args) == 2:
        def server_found(*args):
            server, ip, port = args

            return server.ip == ip and server.port == port
    else:
        raise ValueError('get_server_by_ip_and_port takes either one IP:port string argument or two IP (string) and port (int) arguments')

    servers = get_servers()

    for server in servers:
        if server_found(server, *args):
            return server

    return None


def get_server_by_name(name):
    """Search for a RWR public server based on its name (partial match)."""
    servers = get_servers()

    name = name.lower()

    for server in servers:
        if name in server.name.lower():
            return server

    return None


def get_all_servers_locations():
    """Return the location of all the servers."""
    servers = get_servers()
    locations = {}

    for server in servers:
        if not server.location.country_code:
            continue

        if server.location.continent_code not in locations:
            locations[server.location.continent_code] = {
                'name': server.location.continent_name,
                'countries': {}
            }

        if server.location.country_code not in locations[server.location.continent_code]['countries']:
            locations[server.location.continent_code]['countries'][server.location.country_code] = server.location.country_name

    ret = []

    for continent_code, continent in locations.items():
        group = {
            'type': 'group',
            'value': 'continent:' + continent_code,
            'label': continent['name'],
            'entries': []
        }

        for country_code, country_name in continent['countries'].items():
            group['entries'].append({
                'value': 'country:' + country_code,
                'label': country_name
            })

        group['entries'] = sorted(group['entries'], key=lambda k: k['label'])

        ret.append(group)

    ret = sorted(ret, key=lambda k: k['label'])

    # Extra location filters
    ret.append({
        'value': 'continent:eu+continent:na',
        'label': 'Europe + North America'
    })

    return ret


def get_all_servers_types():
    """Return the type of all of the servers."""
    ret = _get_list(
        lambda server: server.type if server.type not in ['vanilla.winter', 'vanilla.desert', 'pvp'] else False,
        lambda server: server.type_name
    )

    # Extra server type filters
    ret.append({
        'value': 'pacific+edelweiss',
        'label': 'RWR: WWII DLCs'
    })

    return ret


def get_all_servers_modes():
    """Return the mode of all of the servers."""
    return _get_list(
        lambda server: server.mode,
        lambda server: server.mode_name_long
    )


def get_all_servers_maps():
    """Return the map of all of the servers."""
    servers = get_servers()
    maps = {}

    for server in servers:
        if not server.map.id:
            continue

        if server.type.startswith('vanilla') or server.type == 'pvp':
            server_type = 'vanilla'
        else:
            server_type = server.type

        if server_type not in maps:
            maps[server_type] = {
                'name': server.type_name,
                'maps': {}
            }

        if server.map.id not in maps[server_type]['maps']:
            maps[server_type]['maps'][server.map.id] = server.map.name_display

    ret = []

    for game_type in maps.values():
        group = {
            'type': 'group',
            'label': game_type['name'],
            'entries': []
        }

        for map_id, map_name in game_type['maps'].items():
            group['entries'].append({
                'value': map_id,
                'label': map_name
            })

        group['entries'] = sorted(group['entries'], key=lambda k: k['label'])

        ret.append(group)

    return sorted(ret, key=lambda k: k['label'])


def filter_servers(**filters):
    """Filter servers corresponding to the given criteria."""
    def _filter_server(server, filters):
        location = filters.get('location', 'any')
        map = filters.get('map', 'any')
        type = filters.get('type', 'any')
        mode = filters.get('mode', 'any')
        dedicated = filters.get('dedicated')
        official = filters.get('official')
        ranked = filters.get('ranked')
        not_empty = filters.get('not_empty')
        not_full = filters.get('not_full')
        database = filters.get('database')
        username = filters.get('username')

        if database and database != server.database:
            return False

        if username and username not in server.players.list:
            return False

        if location != 'any':
            location_list = location.split('+')
            location_list_matches = []

            for location_in_list in location_list:
                if ':' in location_in_list:
                    location_type, location_code = location_in_list.split(':', maxsplit=1)
                else:
                    location_type = 'country'
                    location_code = location_in_list

                if location_type == 'continent':
                    location_list_matches.append(location_code == server.location.continent_code)
                elif location_type == 'country':
                    location_list_matches.append(location_code == server.location.country_code)

            if True not in location_list_matches:
                return False

        if map != 'any' and map != server.map.id:
            return False

        if type != 'any':
            type_list = type.split('+')
            type_list_matches = []

            for type_in_list in type_list:
                if type_in_list.startswith('vanilla'):
                    type_list_matches.append(server.type.startswith('vanilla'))
                else:
                    type_list_matches.append(type_in_list == server.type)

            if True not in type_list_matches:
                return False

        if mode != 'any' and mode != server.mode:
            return False

        if dedicated == 'yes' and not server.is_dedicated:
            return False

        if official == 'yes' and not server.is_official:
            return False

        if ranked == 'yes' and not server.is_ranked:
            return False

        if not_empty == 'yes' and server.players.current == 0:
            return False

        if not_full == 'yes' and server.players.free == 0:
            return False

        return True

    servers = [server for server in get_servers() if _filter_server(server, filters)]

    limit = filters.get('limit')

    if limit:
        return servers[:limit]

    return servers


def get_counters():
    """Get the number of players online, the active servers as well as the total number of online servers."""
    servers = get_servers()

    online_players = sum([server.players.current for server in servers])
    active_servers = sum([1 for server in servers if server.players.current > 0])
    total_servers = len(servers)

    return (online_players, active_servers, total_servers)


@cache.memoize(timeout=app.config['PLAYERS_CACHE_TIMEOUT'])
def get_players(database, sort=constants.PlayersSort.SCORE.value, target=None, start=0, limit=app.config['LIST_PAGE_SIZES'][0]):
    """Get and parse a list of RWR players."""
    if limit > 100:
        raise ValueError('limit cannot be greater than 100')
    elif limit <= 0:
        raise ValueError('limit cannot be equal or lower than 0')

    if start < 0:
        raise ValueError('start cannot be lower than 0')

    if database not in constants.VALID_DATABASES:
        raise ValueError('database is invalid')

    params = {
        'db': database,
        'sort': sort,
        'start': start,
        'size': limit,
        'search': target
    }

    html_content = _call(
        players_base_url + 'view_players.php',
        parser='html',
        params=params
    )

    players = [Player.load(database, node) for node in html_content.xpath('//table/tr[position() > 1]')]

    if target and target not in [player.username for player in players]:
        return []

    return players


def get_players_by_steam_id(steam_id, only_this_database=None):
    """Get the list of RWR usernames linked to a given Steam ID. Both Invasion and WWII DLCs databases are queried."""
    steam_id_parsed = SteamID(steam_id)
    players = {}

    for database in constants.VALID_DATABASES:
        if only_this_database and database != only_this_database:
            continue

        params = {
            'db': database,
            'key': 'sid',
            'value': steam_id_parsed.as_32
        }

        html_content = _call(
            app.config['RWR_ACCOUNTS_BY_STEAM_ID_ENDPOINT'],
            parser='html',
            params=params,
            auth=app.config['RWR_ACCOUNTS_ENDPOINTS_CREDENTIALS'],
            verify=False
        )

        cells = html_content.xpath('//table/tr[position() > 1]/td[position() = 2]')

        players[database] = [cell.text.strip('\'') for cell in cells if cell.text]

    return players


def delete_player(realm, hash):
    """Delete a given RWR player from the official servers."""
    params = {
        'realm': realm,
        'hash': hash
    }

    xml_content = _call(
        app.config['RWR_ACCOUNTS_DELETE_ENDPOINT'],
        parser='xml',
        params=params,
        auth=app.config['RWR_ACCOUNTS_ENDPOINTS_CREDENTIALS'],
        verify=False
    )

    return dict(xml_content.attrib)


@cache.memoize(timeout=app.config['PLAYERS_CACHE_TIMEOUT'])
def search_player_by_username(database, username, check_exist_only=False):
    """Search for a RWR player (exact match)."""
    if database not in constants.VALID_DATABASES:
        raise ValueError('database is invalid')

    username = username.upper()

    params = {
        'db': database,
        'search': username
    }

    html_content = _call(
        players_base_url + 'view_player.php',
        parser='html',
        params=params
    )

    node = html_content.xpath('(//table/tr[position() = 2])[1]')

    if check_exist_only:
        return False if not node else True
    else:
        if not node:
            return None

        return Player.load(database, node[0], alternative=True)


def get_current_server_of_player(target_username):
    """Return the server where the specified player is playing on, if any (partial match)."""
    servers = get_servers()

    target_username = target_username.lower()
    real_username = target_username
    found_server = None

    for server in servers:
        if not server.players.list:
            continue

        players_list = [player.lower() for player in server.players.list]

        for player in players_list:
            if target_username in player:
                real_username = player
                found_server = server

    return real_username.upper(), found_server
