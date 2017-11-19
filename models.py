from sqlalchemy_utils import ArrowType
from sqlalchemy import func
from rwrs import db, cache, app
from helpers import *
import arrow


class ServerPlayerCount(db.Model):
    class ServerPlayerCountQuery(db.Query):
        def _get_base_count_query(self, count):
            one_month_ago = arrow.utcnow().shift(months=-1)

            query = self.with_entities(ServerPlayerCount.measured_at.label('t'), count)

            return query.filter(ServerPlayerCount.measured_at >= one_month_ago).group_by('t')

        def get_player_count(self, ip=None, port=None):
            query = self._get_base_count_query(func.sum(ServerPlayerCount.count).label('c'))

            if ip and port:
                query = query.filter(ServerPlayerCount._ip == ip, ServerPlayerCount.port == port)

            return query.all()

        def get_server_count(self, active_only=False):
            query = self._get_base_count_query(func.count('*').label('c'))

            if active_only:
                query = query.filter(ServerPlayerCount.count > 0)

            return query.all()

        def get_old_entries(self):
            """Return entries older than one month (exclusive)."""
            one_month_ago = arrow.utcnow().shift(months=-1)

            return self.filter(ServerPlayerCount.measured_at < one_month_ago).all()

    __tablename__ = 'servers_player_count'
    __bind_key__ = 'servers_player_count'
    __table_args__ = (db.Index('ip_port_idx', 'ip', 'port'), )
    query_class = ServerPlayerCountQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # TODO To remove because useless not efficient

    _ip = db.Column('ip', db.Integer, nullable=False)
    port = db.Column(db.Integer, nullable=False)
    measured_at = db.Column(ArrowType, default=arrow.utcnow(), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    @property
    def ip(self):
        if self._ip:
            return long2ip(self._ip)

    @ip.setter
    def ip(self, value):
        if value:
            self._ip = ip2long(value)

    @staticmethod
    def _transform_data(rows):
        return [{'t': row[0].format('YYYY-MM-DDTHH:mm:ss'), 'c': row[1]} for row in rows]

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def server_players_data(ip=None, port=None):
        """Return the servers players chart data, optionally filtering by a server's IP and port."""
        if ip:
            ip = ip2long(ip)

        return ServerPlayerCount._transform_data(ServerPlayerCount.query.get_player_count(ip, port))

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def servers_data(active_only=False):
        """Return the servers chart data, optionally filtering by active servers only."""
        return ServerPlayerCount._transform_data(ServerPlayerCount.query.get_server_count(active_only))

    def __repr__(self):
        return 'ServerPlayerCount:' + self.id
