from sqlalchemy_utils import ArrowType
from rwrs import db
from helpers import *
import arrow


class ServerPlayerCount(db.Model):
    TIMESPAN_LAST_DAY = 1
    TIMESPAN_LAST_WEEK = 2
    TIMESPAN_LAST_MONTH = 3

    class ServerPlayerCountQuery(db.Query):
        def _get_base_count_query(self, timespan):
            pass # TODO

        def get_player_count(self, timespan, ip=None, port=None):
            pass # TODO

        def get_server_count(self, timespan, online_only=False):
            pass # TODO

    __tablename__ = 'servers_player_count'
    __bind_key__ = 'servers_player_count'
    __table_args__ = (db.Index('ip_port_idx', 'ip', 'port'), )
    query_class = ServerPlayerCountQuery

    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # TODO To remove because useless

    _ip = db.Column('ip', db.Integer, nullable=False)
    port = db.Column(db.Integer, nullable=False)
    measured_at = db.Column(ArrowType, default=arrow.utcnow(), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    def __init__(self, ip=None, port=None, measured_at=arrow.utcnow(), count=None):
        self.ip = ip
        self.port = port
        self.measured_at = measured_at
        self.count = count

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
