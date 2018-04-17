from sqlalchemy.util import memoized_property
from sqlalchemy_utils import ArrowType
from rwrs import db, cache, app
from sqlalchemy import func
from enum import Enum
import rwr.constants
import helpers
import arrow


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
        return helpers.long2ip(self._ip) if self._ip else None

    @ip.setter
    def ip(self, value):
        if value:
            self._ip = helpers.ip2long(value)

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def server_players_data(ip=None, port=None):
        """Return the servers players chart data, optionally filtering by a server's IP and port."""
        if ip:
            ip = helpers.ip2long(ip)

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


class RwrRootServerStatus(Enum):
    UP = 'UP'
    DOWN = 'DOWN'


class RwrRootServer(db.Model):
    __tablename__ = 'rwr_root_servers'
    __table_args__ = (db.Index('host_idx', 'host'), )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    host = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(RwrRootServerStatus), nullable=False)

    @property
    def status_icon(self):
        if self.status == RwrRootServerStatus.UP:
            return 'check'
        elif self.status == RwrRootServerStatus.DOWN:
            return 'times'

    @property
    def status_text(self):
        if self.status == RwrRootServerStatus.UP:
            return 'Up'
        elif self.status == RwrRootServerStatus.DOWN:
            return 'Down'

    @property
    def status_color(self):
        if self.status == RwrRootServerStatus.UP:
            return 'green'
        elif self.status == RwrRootServerStatus.DOWN:
            return 'red'

    @staticmethod
    def get_data_for_display():
        servers_statuses = rwr.constants.ROOT_RWR_SERVERS

        root_servers = RwrRootServer.query.all()
        servers_down_count = 0

        for group in servers_statuses:
            group['status_icon'] = 'check'
            group['status_text'] = 'Everything operating normally'
            group['status_color'] = 'green'

            group_servers_down_count = 0

            for server in group['servers']:
                server['status_icon'] = 'question'
                server['status_text'] = 'Status unknown'
                server['status_color'] = 'grey'

                for root_server in root_servers:
                    if root_server.host == server['host']:
                        server['status_icon'] = root_server.status_icon
                        server['status_text'] = root_server.status_text
                        server['status_color'] = root_server.status_color

                        if root_server.status == RwrRootServerStatus.DOWN:
                            servers_down_count += 1
                            group_servers_down_count += 1

                        break

            group['is_everything_ok'] = group_servers_down_count == 0

            if group_servers_down_count == len(group['servers']):
                group['status_icon'] = 'times'
                group['status_text'] = 'Major outage'
                group['status_color'] = 'red'
            elif group_servers_down_count > 0 and group_servers_down_count < len(group['servers']):
                group['status_icon'] = 'exclamation'
                group['status_text'] = 'Partial outage'
                group['status_color'] = 'orange'

        is_everything_ok = servers_down_count == 0

        return (is_everything_ok, servers_statuses)

    def __repr__(self):
        return 'RwrRootServer:' + self.id


class VariableType(Enum):
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    STRING = 'STRING'
    BOOL = 'BOOL'
    ARROW = 'ARROW'


class Variable(db.Model):
    __tablename__ = 'variables'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.Enum(VariableType), nullable=False)
    _value = db.Column('value', db.String)

    @property
    def value(self):
        """Get the real (cast) value of this Variable."""
        if self._value and self.type != VariableType.STRING: # No need to cast STRING values as they are stored as string in the DB
            if self.type == VariableType.INTEGER:
                return int(self._value)
            elif self.type == VariableType.FLOAT:
                return float(self._value)
            elif self.type == VariableType.BOOL:
                return bool(int(self._value))
            elif self.type == VariableType.ARROW:
                return arrow.get(self._value)
            else:
                raise ValueError('Unhandled value type')

        return self._value

    @value.setter
    def value(self, value):
        """Set the value an d type of this Variable."""
        if isinstance(value, int):
            self.type = VariableType.INTEGER
            self._value = str(value)
        elif isinstance(value, float):
            self.type = VariableType.FLOAT
            self._value = str(value)
        elif isinstance(value, str):
            self.type = VariableType.STRING
            self._value = value
        elif isinstance(value, bool):
            self.type = VariableType.BOOL
            self._value = str(int(value))
        elif isinstance(value, arrow.Arrow):
            self.type = VariableType.ARROW
            self._value = value.format()
        else:
            raise ValueError('Unhandled value type')

    @staticmethod
    def get_value(name):
        """Get the value of the Variable corresponding to the given name.

        Return None if the Variable doesn't exists or its value is empty."""
        var = Variable.query.filter(Variable.name == name).first()

        return var.value if var else None

    @staticmethod
    def get_many_values(names):
        """Get the values of several Variables corresponding to the given names.

        Variable key may not be present if it doesn't exists."""
        return {var.name: var.value for var in Variable.query.filter(Variable.name.in_(names)).all()}

    @staticmethod
    def set_value(name, value):
        """Set the value of the Variable corresponding to the given name.

        If the Variable doesn't exists, it is created. Commiting DB operation is needed after calling this method."""
        var = Variable.query.filter(Variable.name == name).first()

        if not var:
            var = Variable()
            var.name = name

        var.value = value

        db.session.add(var)

    @staticmethod
    def set_many_values(names_and_values):
        """Set the value of several Variables corresponding to the given names.

        If a Variable doesn't exists, it is created. Commiting DB operation is needed after calling this method."""
        if not names_and_values:
            return

        existing_vars = {var.name: var for var in Variable.query.filter(Variable.name.in_(names_and_values.keys())).all()}

        for name, value in names_and_values.items():
            if name in existing_vars:
                var = existing_vars[name]
            else:
                var = Variable()
                var.name = name

            var.value = value

            db.session.add(var)

    @staticmethod
    def get_peaks_for_display():
        """Return the list of peak players and servers counts for display."""
        var_names = [
            'total_players_peak_count', 'total_players_peak_date',
            'online_players_peak_count', 'online_players_peak_date',
            'online_servers_peak_count', 'online_servers_peak_date',
            'active_servers_peak_count', 'active_servers_peak_date'
        ]

        peaks = Variable.get_many_values(var_names)

        for name in var_names:
            if name not in peaks:
                peaks[name] = '?'
            elif name.endswith('_date'):
                    peaks[name] = peaks[name].format('MMM D, YYYY')

        return peaks

    def __repr__(self):
        return 'Variable:' + self.id


class RwrAccountType(Enum):
    INVASION = 'INVASION'
    PACIFIC = 'PACIFIC'


class RwrAccount(db.Model):
    __tablename__ = 'rwr_accounts'
    __table_args__ = (db.Index('type_username_idx', 'type', 'username'), )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    type = db.Column(db.Enum(RwrAccountType), nullable=False)
    username = db.Column(db.String(16), nullable=False)
    created_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), nullable=False)
    updated_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), nullable=False)

    @memoized_property
    def stats(self):
        """Return a query which have to be executed to get all RwrAccountStat linked to this RwrAccount."""
        return RwrAccountStat.query.filter(RwrAccountStat.rwr_account_id == self.id).order_by(RwrAccountStat.created_at.desc())

    @memoized_property
    def has_stats(self):
        """Determine is this RwrAccount object have at least one RwrAccountStat."""
        return RwrAccountStat.query.with_entities(func.count('*')).filter(RwrAccountStat.rwr_account_id == self.id).scalar() > 0

    def __repr__(self):
        return 'RwrAccount:' + self.id


class RwrAccountStat(db.Model):
    __tablename__ = 'rwr_account_stats'
    __bind_key__ = 'rwr_account_stats'
    __table_args__ = (db.Index('rwr_account_id_idx', 'rwr_account_id'), )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    leaderboard_position = db.Column(db.Integer, nullable=False)
    xp = db.Column(db.Integer, nullable=False)
    kills = db.Column(db.Integer, nullable=False)
    deaths = db.Column(db.Integer, nullable=False)
    time_played = db.Column(db.Integer, nullable=False)
    longest_kill_streak = db.Column(db.Integer, nullable=False)
    targets_destroyed = db.Column(db.Integer, nullable=False)
    vehicles_destroyed = db.Column(db.Integer, nullable=False)
    soldiers_healed = db.Column(db.Integer, nullable=False)
    teamkills = db.Column(db.Integer, nullable=False)
    distance_moved = db.Column(db.Float, nullable=False)
    shots_fired = db.Column(db.Integer, nullable=False)
    throwables_thrown = db.Column(db.Integer, nullable=False)
    created_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), nullable=False)

    rwr_account_id = db.Column(db.Integer, nullable=False) # Weak foreign key to the rwr_accounts located in another DB

    @memoized_property
    def rwr_account(self):
        """Return the RwrAccount object linked to this RwrAccountStat."""
        return RwrAccount.query.get(self.rwr_account_id)

    @memoized_property
    def score(self):
        return self.kills - self.deaths

    @memoized_property
    def kd_ratio(self):
        return round(self.kills / self.deaths, 2)

    @memoized_property
    def leaderboard_position_display(self):
        return helpers.humanize_integer(self.leaderboard_position)

    @memoized_property
    def xp_display(self):
        return helpers.humanize_integer(self.xp)

    @memoized_property
    def kills_display(self):
        return helpers.humanize_integer(self.kills)

    @memoized_property
    def deaths_display(self):
        return helpers.humanize_integer(self.deaths)

    @memoized_property
    def time_played_display(self):
        return helpers.humanize_seconds_to_hours(self.time_played)

    @memoized_property
    def score_display(self):
        return helpers.humanize_integer(self.score)

    @memoized_property
    def longest_kill_streak_display(self):
        return helpers.humanize_integer(self.longest_kill_streak)

    @memoized_property
    def targets_destroyed_display(self):
        return helpers.humanize_integer(self.targets_destroyed)

    @memoized_property
    def vehicles_destroyed_display(self):
        return helpers.humanize_integer(self.vehicles_destroyed)

    @memoized_property
    def soldiers_healed_display(self):
        return helpers.humanize_integer(self.soldiers_healed)

    @memoized_property
    def teamkills_display(self):
        return helpers.humanize_integer(self.teamkills)

    @memoized_property
    def shots_fired_display(self):
        return helpers.humanize_integer(self.shots_fired)

    @memoized_property
    def throwables_thrown_display(self):
        return helpers.humanize_integer(self.throwables_thrown)

    def __repr__(self):
        return 'RwrAccountStat:' + self.id
