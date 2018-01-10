from sqlalchemy_utils import ArrowType
from rwrs import db, cache, app
from sqlalchemy import func
from helpers import *
import arrow

__all__ = [
    'ServerPlayerCount',
    'SteamPlayerCount'
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
