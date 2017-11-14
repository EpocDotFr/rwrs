from sqlalchemy_utils import ArrowType
from sqlalchemy import func
from helpers import *
from rwrs import db
import arrow


class ServerPlayerCount(db.Model):
    TIMESPAN_LAST_DAY = 1
    TIMESPAN_LAST_WEEK = 2
    TIMESPAN_LAST_MONTH = 3

    class ServerPlayerCountQuery(db.Query):
        def _apply_timespan_filters(self, query, timespan):
            now = arrow.utcnow()

            if timespan == ServerPlayerCount.TIMESPAN_LAST_DAY:
                # TODO select strftime('%H:%M', `measured_at`) AS `time`
                past = now.shift(days=-1)
            elif timespan == ServerPlayerCount.TIMESPAN_LAST_WEEK:
                # TODO select strftime('%w', `measured_at`) AS `time`
                past = now.shift(weeks=-1)
            elif timespan == ServerPlayerCount.TIMESPAN_LAST_MONTH:
                # TODO select DATE(`measured_at`) AS `time`
                past = now.shift(months=-1)

            return query.filter(ServerPlayerCount.measured_at >= past)
            # TODO group by `time`

        def get_player_count(self, timespan, ip=None, port=None):
            query = self.with_entities(func.sum(ServerPlayerCount.count).label('count'))
            query = self._apply_timespan_filters(query, timespan)

            if ip and port:
                query = query.filter(ServerPlayerCount.ip == ip and ServerPlayerCount.port == port)

            return query.all()

        def get_server_count(self, timespan, active_only=False):
            query = self.with_entities(func.count('*').label('count'))
            query = self._apply_timespan_filters(query, timespan)

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

    def __repr__(self):
        return 'ServerPlayerCount:' + self.id
