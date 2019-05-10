from sqlalchemy.util import memoized_property
from flask import url_for, current_app
from flask_login import current_user
from . import constants, utils
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

        ret.name = name_node.text.strip() if name_node.text else 'N/A'
        ret.ip = address_node.text
        ret.port = int(port_node.text)

        server_type, map_id = utils.parse_map_path(map_id_node.text.replace('//', '/'))

        ret.type = server_type

        ret.map = ServerMap()
        ret.map.id = map_id

        if ret.type in constants.MAPS and ret.map.id in constants.MAPS[ret.type]:
            target_map = constants.MAPS[ret.type][ret.map.id]

            ret.map.name = target_map['name']
            ret.map.has_minimap = target_map['has_minimap']
            ret.map.has_preview = target_map['has_preview']

            if ret.map.has_preview:
                if current_app:
                    ret.map.set_preview_image_urls(ret.type)
                else:
                    with app.app_context():
                        ret.map.set_preview_image_urls(ret.type)

            if ret.map.has_minimap:
                if current_app:
                    ret.map.set_minimap_image_urls(ret.type)
                else:
                    with app.app_context():
                        ret.map.set_minimap_image_urls(ret.type)

        ret.map.name_display = ret.map.name if ret.map.name else ret.map.id

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
        ret.realm = realm_node.text

        ret.location = ServerLocation()

        html_server_node = html_servers.xpath('(//table/tr[(td[3] = \'{ip}\') and (td[4] = \'{port}\')])[1]'.format(ip=ret.ip, port=ret.port))

        if html_server_node:
            html_server_node = html_server_node[0]

            players_node = html_server_node[11]

            if players_node.text:
                ret.players.list = [player_name.strip() for player_name in players_node.text.split(',')]
                ret.players.list.sort()

        if current_app:
            ret.set_links()
            ret.set_images()
        else:
            with app.app_context():
                ret.set_links()
                ret.set_images()

        return ret

    @memoized_property
    def name_slug(self):
        return slugify(self.name)

    @memoized_property
    def name_display(self):
        return '{}{}{}'.format(
            '⭐️ ' if self.is_ranked else '',
            '📅 ' if self.event else '',
            self.name
        )

    @memoized_property
    def summary(self):
        return '{}/{} • {} • {}'.format(
            self.players.current,
            self.players.max,
            self.type_name,
            self.map.name_display
        )

    @memoized_property
    def ip_and_port(self):
        return '{ip}:{port}'.format(ip=self.ip, port=self.port)

    @memoized_property
    def type_name(self):
        return utils.get_type_name(self.type)

    @memoized_property
    def mode_name(self):
        return utils.get_mode_name(self.mode)

    @memoized_property
    def mode_name_long(self):
        return utils.get_mode_name(self.mode, False)

    @memoized_property
    def is_ranked(self):
        return self.realm in [database['realm'] for _, database in constants.PLAYERS_LIST_DATABASES.items()]

    @memoized_property
    def steam_join_link(self):
        return 'steam://rungameid/{gameid}//server_address={ip} server_port={port}'.format(
            gameid=app.config['RWR_STEAM_APP_ID'],
            ip=self.ip,
            port=self.port
        )

    def set_links(self):
        """Set the relative and absolute URLs of this server's details page."""
        params = {
            'ip': self.ip,
            'port': self.port,
            'slug': self.name_slug
        }

        self.link = url_for('server_details', **params)
        self.link_absolute = url_for('server_details', **params, _external=True)

    def set_images(self):
        """Set the relative and absolute URLs to the images of this Server."""
        if not self.is_dedicated:
            self.banner = None
            self.banner_absolute = None

            return

        params = {
            'ip': self.ip,
            'port': self.port
        }

        self.banner = url_for('dynamic_server_image', **params)
        self.banner_absolute = url_for('dynamic_server_image', **params, _external=True)

    @memoized_property
    def database(self):
        """The players list database name of this server."""
        if self.is_ranked:
            for database_name, database in constants.PLAYERS_LIST_DATABASES.items():
                if database['realm'] == self.realm:
                    return database_name

        return None

    @memoized_property
    def database_name(self):
        return utils.get_database_name(self.database)

    @memoized_property
    def have_friends_from_current_user(self):
        """Determine whether this server have friends from the current player or not."""
        if not current_user.is_authenticated:
            return False

        for friend in current_user.ordered_friends:
            if friend.username in self.players.list:
                return True

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

    def set_minimap_image_urls(self, game_type):
        """Set the relative and absolute URLs to the minimap image of this map."""
        params = {
            'game_type': game_type,
            'map_id': self.id
        }

        minimap_url = 'images/maps/minimap/{game_type}/{map_id}.png'.format(**params)

        self.minimap = url_for('static', filename=minimap_url)
        self.minimap_absolute = url_for('static', filename=minimap_url, _external=True)


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
    text = None

    def set_flags(self):
        if not self.country_code:
            return

        params = {
            'country_code': self.country_code.upper(),
        }

        flag_url = 'images/flags/{country_code}.png'.format(**params)

        self.flag = url_for('static', filename=flag_url)
        self.flag_absolute = url_for('static', filename=flag_url, _external=True)

    def __repr__(self):
        return 'ServerLocation:' + self.country_code
