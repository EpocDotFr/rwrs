from sqlalchemy_utils import ArrowType
from helpers import *
from rwrs import db
import arrow


class ServerPlayerCount(db.Model):
    TIMESPAN_LAST_DAY = 1
    TIMESPAN_LAST_WEEK = 2
    TIMESPAN_LAST_MONTH = 3

    class ServerPlayerCountQuery(db.Query):
        def _get_base_query(self, timespan):
            now = arrow.utcnow()
            q = self

            if timespan == ServerPlayerCount.TIMESPAN_LAST_DAY:
                past = now.shift(days=-1)
            elif timespan == ServerPlayerCount.TIMESPAN_LAST_WEEK:
                past = now.shift(weeks=-1)
            elif timespan == ServerPlayerCount.TIMESPAN_LAST_MONTH:
                past = now.shift(months=-1)

            return q.filter(ServerPlayerCount.measured_at >= past)

        def get_player_count(self, timespan, ip=None, port=None):
            q = self._get_base_query(timespan)

            if ip and port:
                q = q.filter(ServerPlayerCount.ip == ip and ServerPlayerCount.port == port)

            return q.all()

        def get_server_count(self, timespan, active_only=False):
            q = self._get_base_query(timespan)

            if active_only:
                q = q.filter(ServerPlayerCount.count > 0)

            return q.all()

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
        return '<ServerPlayerCount> {}:{}'.format(self.ip, self.port)
