from flask import url_for, current_app
from . import constants, utils
from geolite2 import geolite2
from slugify import slugify
from rwrs import app


class Server:
    database = None

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

        ret.name = name_node.text.strip()
        ret.name_slug = slugify(ret.name)

        ret.ip = address_node.text
        ret.port = int(port_node.text)
        ret.ip_and_port = '{ip}:{port}'.format(ip=ret.ip, port=ret.port)

        server_type, map_id = utils.parse_map_path(map_id_node.text.replace('//', '/'))

        ret.type = server_type
        ret.type_name = utils.get_type_name(ret.type)

        ret.map = ServerMap()
        ret.map.id = map_id

        if ret.type in constants.MAPS and ret.map.id in constants.MAPS[ret.type]:
            target_map = constants.MAPS[ret.type][ret.map.id]

            ret.map.name = target_map['name']
            ret.map.has_minimap = target_map['has_minimap']
            ret.map.has_preview = target_map['has_preview']
            ret.map.name_display = ret.map.name if ret.map.name else ret.map.id

            if ret.map.has_preview:
                if current_app:
                    ret.map.set_preview_image_urls(ret.type)
                else:
                    with app.app_context():
                        ret.map.set_preview_image_urls(ret.type)

        ret.bots = int(bots_node.text)

        ret.players = ServerPlayers()
        ret.players.current = 0 if int(current_players_node.text) < 0 else int(current_players_node.text)
        ret.players.max = int(max_players_node.text)
        ret.players.free = ret.players.max - ret.players.current

        ret.version = version_node.text
        ret.is_dedicated = True if dedicated_node.text == '1' else False
        ret.comment = comment_node.text.strip() if comment_node.text else None
        ret.website = url_node.text.strip() if url_node.text else None

        ret.mode = mode_node.text
        ret.mode_name = utils.get_mode_name(ret.mode)
        ret.mode_name_long = utils.get_mode_name(ret.mode, False)

        ret.realm = realm_node.text
        ret.is_ranked = ret.realm in [database['realm'] for _, database in constants.PLAYERS_LIST_DATABASES.items()]
        ret.database = ret.get_database()
        ret.database_name = utils.get_database_name(ret.database)

        ret.location = ServerLocation()

        with geolite2 as gl2:
            location = gl2.reader().get(ret.ip)

            if location:
                if 'city' in location:
                    ret.location.city_name = location['city']['names']['en']

                ret.location.country_code = location['country']['iso_code'].lower()
                ret.location.country_name = location['country']['names']['en']
                ret.location.continent_code = location['continent']['code'].lower()
                ret.location.continent_name = location['continent']['names']['en']

        ret.steam_join_link = 'steam://rungameid/270150//server_address={ip} server_port={port}'.format(ip=ret.ip, port=ret.port)

        html_server_node = html_servers.xpath('(//table/tr[(td[3] = \'{ip}\') and (td[4] = \'{port}\')])[1]'.format(ip=ret.ip, port=ret.port))

        if html_server_node:
            html_server_node = html_server_node[0]

            players_node = html_server_node[11]

            if players_node.text:
                ret.players.list = [player_name.strip() for player_name in players_node.text.split(',')]
                ret.players.list.sort()

        ret.name_display = '⭐️ ' + ret.name if ret.is_ranked else ret.name
        ret.summary = '{} - {} - {}/{}'.format(
            ret.type_name,
            ret.map.name_display,
            ret.players.current,
            ret.players.max
        )

        if current_app:
            ret.set_links()
        else:
            with app.app_context():
                ret.set_links()

        return ret

    def set_links(self):
        """Set the relative and absolute URLs of this server's details page."""
        self.link = url_for('server_details', ip=self.ip, port=self.port, slug=self.name_slug)
        self.link_absolute = url_for('server_details', ip=self.ip, port=self.port, slug=self.name_slug, _external=True)

    def get_database(self):
        """Return the players list database name of this server."""
        if self.is_ranked:
            for database_name, database in constants.PLAYERS_LIST_DATABASES.items():
                if database['realm'] == self.realm:
                    return database_name

        return None

    def __repr__(self):
        return 'Server:' + self.ip_and_port


class ServerMap:
    name = None
    has_minimap = False
    has_preview = False

    def __repr__(self):
        return 'ServerMap:' + self.id

    def set_preview_image_urls(self, game_type):
        """Set the relative and absolute URLs to the preview image of this map."""
        params = {
            'game_type': game_type,
            'map_id': self.id
        }

        preview_url = 'images/maps/preview/{game_type}/{map_id}.png'.format(**params)

        self.preview = url_for('static', filename=preview_url)
        self.preview_absolute = url_for('static', filename=preview_url, _external=True)


class ServerPlayers:
    current = 0
    max = 0
    free = 0
    list = []


class ServerLocation:
    city_name = None
    country_code = None
    country_name = None
    continent_code = None
    continent_name = None

    def __repr__(self):
        return 'ServerLocation:' + self.country_code
