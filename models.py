from sqlalchemy_utils import ArrowType
from sqlalchemy import func
from rwrs import db, cache, app
from helpers import *
import arrow


class ServerPlayerCount(db.Model):
    TIMESPAN_LAST_DAY = 1
    TIMESPAN_LAST_WEEK = 2
    TIMESPAN_LAST_MONTH = 3

    class ServerPlayerCountQuery(db.Query):
        def _apply_timespan_filters(self, query, timespan, count):
            now = arrow.utcnow()

            if timespan == ServerPlayerCount.TIMESPAN_LAST_DAY:
                past = now.shift(days=-1)
                fmt = '%H:%M'
            elif timespan == ServerPlayerCount.TIMESPAN_LAST_WEEK:
                past = now.shift(weeks=-1)
                fmt = '%w'
            elif timespan == ServerPlayerCount.TIMESPAN_LAST_MONTH:
                past = now.shift(months=-1)
                fmt = '%Y-%m-%d'

            query = query.with_entities(func.strftime(fmt, ServerPlayerCount.measured_at).label('time'), count)
            query = query.filter(ServerPlayerCount.measured_at >= past)

            return query.group_by('time')

        def get_player_count(self, timespan, ip=None, port=None):
            query = self._apply_timespan_filters(self, timespan, func.sum(ServerPlayerCount.count).label('count'))

            if ip and port:
                query = query.filter(ServerPlayerCount.ip == ip and ServerPlayerCount.port == port)

            return query.all()

        def get_server_count(self, timespan, active_only=False):
            query = self._apply_timespan_filters(self, timespan, func.count('*').label('count'))

            if active_only:
                query = query.filter(ServerPlayerCount.count > 0)

            return query.all()

        def get_old_entries(self):
            """Return entries older than one month (exclusive)."""
            return self.filter(ServerPlayerCount.measured_at > arrow.utcnow().shift(months=-1)).all()

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
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def server_players_data(ip, port):
        ip = ip2long(ip)

        return {
            'last_day': ServerPlayerCount.query.get_player_count(ServerPlayerCount.TIMESPAN_LAST_DAY, ip, port),
            'last_week': ServerPlayerCount.query.get_player_count(ServerPlayerCount.TIMESPAN_LAST_WEEK, ip, port),
            'last_month': ServerPlayerCount.query.get_player_count(ServerPlayerCount.TIMESPAN_LAST_MONTH, ip, port)
        }

    def __repr__(self):
        return 'ServerPlayerCount:' + self.id
