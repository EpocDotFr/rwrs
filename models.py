from sqlalchemy_utils import ArrowType
from rwrs import db, cache, app
from sqlalchemy import func
from enum import Enum
from helpers import *
import rwr.constants
import arrow

__all__ = [
    'ServerPlayerCount',
    'SteamPlayerCount',
    'RwrMasterServerStatus',
    'RwrMasterServer'
]


class Measurable:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # TODO To remove because useless and non-efficient

    measured_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    @staticmethod
    def transform_data(rows):
        """Given a list of date => integer, convert the date to a string format."""
        return [{'t': row[0].format('YYYY-MM-DDTHH:mm:ss'), 'c': row[1]} for row in rows]

    @staticmethod
    def past():
        """Return an Arrow object one week in the past."""
        return arrow.utcnow().floor('minute').shift(weeks=-1)


class ServerPlayerCount(db.Model, Measurable):
    class ServerPlayerCountQuery(db.Query):
        def _get_base_count_query(self, count):
            """Return the base query used to get the count."""
            q = self.with_entities(ServerPlayerCount.measured_at.label('t'), count)

            return q.filter(ServerPlayerCount.measured_at >= Measurable.past()).group_by('t')

        def get_player_count(self, ip=None, port=None):
            """Return the online players count, optionally filtered by a server's IP and port."""
            q = self._get_base_count_query(func.sum(ServerPlayerCount.count).label('c'))

            if ip and port:
                q = q.filter(ServerPlayerCount._ip == ip, ServerPlayerCount.port == port)

            return q.all()

        def get_server_count(self, active_only=False):
            """Return the online servers count, optionally filtered by the active ones only."""
            q = self._get_base_count_query(func.count('*').label('c'))

            if active_only:
                q = q.filter(ServerPlayerCount.count > 0)

            return q.all()

        def get_old_entries(self):
            """Return entries older than 1 weeks (exclusive)."""
            return self.filter(ServerPlayerCount.measured_at < Measurable.past()).all()

    __tablename__ = 'servers_player_count'
    __bind_key__ = 'servers_player_count'
    __table_args__ = (db.Index('ip_port_idx', 'ip', 'port'), )
    query_class = ServerPlayerCountQuery

    _ip = db.Column('ip', db.Integer, nullable=False)
    port = db.Column(db.Integer, nullable=False)

    @property
    def ip(self):
        return long2ip(self._ip) if self._ip else None

    @ip.setter
    def ip(self, value):
        if value:
            self._ip = ip2long(value)

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def server_players_data(ip=None, port=None):
        """Return the servers players chart data, optionally filtering by a server's IP and port."""
        if ip:
            ip = ip2long(ip)

        return Measurable.transform_data(ServerPlayerCount.query.get_player_count(ip, port))

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def servers_data(active_only=False):
        """Return the servers chart data, optionally filtering by active servers only."""
        return Measurable.transform_data(ServerPlayerCount.query.get_server_count(active_only))

    def __repr__(self):
        return 'ServerPlayerCount:' + self.id


class SteamPlayerCount(db.Model, Measurable):
    class SteamPlayerCountQuery(db.Query):
        def get_player_count(self):
            """Return the Steam players count."""
            q = self.with_entities(SteamPlayerCount.measured_at.label('t'), SteamPlayerCount.count.label('c'))
            q = q.filter(SteamPlayerCount.measured_at >= Measurable.past()).group_by('t')

            return q.all()

        def get_old_entries(self):
            """Return entries older than 1 weeks (exclusive)."""
            return self.filter(SteamPlayerCount.measured_at < Measurable.past()).all()

    __tablename__ = 'steam_players_count'
    __bind_key__ = 'steam_players_count'
    query_class = SteamPlayerCountQuery

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def players_data():
        """Return the Steam players count chart data."""
        return Measurable.transform_data(SteamPlayerCount.query.get_player_count())

    def __repr__(self):
        return 'SteamPlayerCount:' + self.id


class RwrMasterServerStatus(Enum):
    UNKNOWN = 'UNKNOWN'
    UP = 'UP'
    DOWN = 'DOWN'


class RwrMasterServer(db.Model):
    class RwrMasterServerQuery(db.Query):
        pass

    __tablename__ = 'rwr_master_servers'
    __table_args__ = (db.Index('host_idx', 'host'), )
    query_class = RwrMasterServerQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    host = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(RwrMasterServerStatus), default=RwrMasterServerStatus.UNKNOWN)

    @property
    def status_icon(self):
        if self.status == RwrMasterServerStatus.UP:
            return 'check'
        elif self.status == RwrMasterServerStatus.DOWN:
            return 'times'
        elif self.status == RwrMasterServerStatus.UNKNOWN:
            return 'question'

    @property
    def status_text(self):
        if self.status == RwrMasterServerStatus.UP:
            return 'OK'
        elif self.status == RwrMasterServerStatus.DOWN:
            return 'Down'
        elif self.status == RwrMasterServerStatus.UNKNOWN:
            return 'Status unknown'

    @property
    def status_color(self):
        if self.status == RwrMasterServerStatus.UP:
            return 'green'
        elif self.status == RwrMasterServerStatus.DOWN:
            return 'red'
        elif self.status == RwrMasterServerStatus.UNKNOWN:
            return 'grey'

    @staticmethod
    def get_data_for_display():
        servers_statuses = rwr.constants.SERVERS_TO_MONITOR

        master_servers = RwrMasterServer.query.all()
        is_everything_ok = True

        for group in servers_statuses:
            for continent in group['continents']:
                continent['status_icon'] = 'check' # exclamation, times
                continent['status_text'] = 'All good' # Partial outage, Major outage
                continent['status_color'] = 'green' # orange, red
                continent['is_everything_ok'] = True

                for server in continent['servers']:
                    server['status_icon'] = 'question'
                    server['status_text'] = 'Status unknown'
                    server['status_color'] = 'grey'

                    for master_server in master_servers:
                        if master_server.host == server['host']:
                            server['status_icon'] = master_server.status_icon
                            server['status_text'] = master_server.status_text
                            server['status_color'] = master_server.status_color

                            if master_server.status == RwrMasterServerStatus.DOWN:
                                continent['status_icon'] = master_server.status_icon
                                continent['status_text'] = 'TODO'
                                continent['status_color'] = master_server.status_color
                                continent['is_everything_ok'] = False

                            break

        return (is_everything_ok, servers_statuses)
