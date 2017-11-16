from sqlalchemy_utils import ArrowType
from sqlalchemy import func
from rwrs import db, cache, app
from helpers import *
import arrow


class ServerPlayerCount(db.Model):
    TIMESPAN_PAST_DAY = 1
    TIMESPAN_PAST_WEEK = 2
    TIMESPAN_PAST_MONTH = 3

    class ServerPlayerCountQuery(db.Query):
        def _get_base_count_query(self, timespan, count):
            now = arrow.utcnow()

            if timespan == ServerPlayerCount.TIMESPAN_PAST_DAY:
                past = now.shift(days=-1)
                fmt = '%Y-%m-%dT%H:%M:00'
            elif timespan == ServerPlayerCount.TIMESPAN_PAST_WEEK:
                past = now.shift(weeks=-1)
                fmt = '%Y-%m-%dT%H:%M:00'
            elif timespan == ServerPlayerCount.TIMESPAN_PAST_MONTH:
                past = now.shift(months=-1)
                fmt = '%Y-%m-%dT%H:%M:00'

            query = self.with_entities(func.strftime(fmt, ServerPlayerCount.measured_at).label('t'), count)
            query = query.filter(ServerPlayerCount.measured_at >= past).group_by('t')

            return query

        def get_player_count(self, timespan, ip=None, port=None):
            query = self._get_base_count_query(timespan, func.sum(ServerPlayerCount.count).label('c'))

            if ip and port:
                query = query.filter(ServerPlayerCount._ip == ip, ServerPlayerCount.port == port)

            return query.all()

        def get_server_count(self, timespan, active_only=False):
            query = self._get_base_count_query(timespan, func.count('*').label('c'))

            if active_only:
                query = query.filter(ServerPlayerCount.count > 0)

            return query.all()

        def get_old_entries(self):
            """Return entries older than one month (exclusive)."""
            one_month_ago = arrow.utcnow().shift(months=-1)

            return self.filter(ServerPlayerCount.measured_at > one_month_ago).all()

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
        return [{'t': row[0], 'c': row[1]} for row in rows]

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def server_players_data(ip=None, port=None):
        """Return the servers players chart data, optionally filtering by a server's IP and port."""
        if ip:
            ip = ip2long(ip)

        return [
            ServerPlayerCount._transform_data(ServerPlayerCount.query.get_player_count(ServerPlayerCount.TIMESPAN_PAST_DAY, ip, port)),
            ServerPlayerCount._transform_data(ServerPlayerCount.query.get_player_count(ServerPlayerCount.TIMESPAN_PAST_WEEK, ip, port)),
            ServerPlayerCount._transform_data(ServerPlayerCount.query.get_player_count(ServerPlayerCount.TIMESPAN_PAST_MONTH, ip, port))
        ]

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def servers_data(active_only=False):
        """Return the servers chart data, optionally filtering by active servers only."""
        return [
            ServerPlayerCount._transform_data(ServerPlayerCount.query.get_server_count(ServerPlayerCount.TIMESPAN_PAST_DAY, active_only)),
            ServerPlayerCount._transform_data(ServerPlayerCount.query.get_server_count(ServerPlayerCount.TIMESPAN_PAST_WEEK, active_only)),
            ServerPlayerCount._transform_data(ServerPlayerCount.query.get_server_count(ServerPlayerCount.TIMESPAN_PAST_MONTH, active_only))
        ]

    def __repr__(self):
        return 'ServerPlayerCount:' + self.id
