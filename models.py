from sqlalchemy.util import memoized_property
from sqlalchemy_utils import ArrowType
from flask import url_for, current_app
from flask_login import UserMixin
from rwrs import db, cache, app
from sqlalchemy import func
from slugify import slugify
from enum import Enum
import rwr.utils
import helpers
import hashlib
import iso3166
import arrow


def one_week_ago():
    """Return an Arrow object 1 week in the past."""
    return arrow.utcnow().floor('minute').shift(weeks=-1)


def one_year_ago():
    """Return an Arrow object 1 year in the past."""
    return arrow.utcnow().floor('day').shift(years=-1)


class Measurable:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # TODO To remove because useless and non-efficient

    measured_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    @staticmethod
    def transform_data(rows, format='YYYY-MM-DDTHH:mm:ss'):
        """Given a list of date => number, convert the date to a string format."""
        return [{'t': row[0].format(format), 'v': row[1]} for row in rows]


class ServerPlayerCount(db.Model, Measurable):
    class ServerPlayerCountQuery(db.Query):
        def _get_base_count_query(self, count):
            """Return the base query used to get the count."""
            q = self.with_entities(ServerPlayerCount.measured_at.label('t'), count)

            return q.filter(ServerPlayerCount.measured_at >= one_week_ago()).group_by('t')

        def get_player_count(self, ip=None, port=None):
            """Return the online players count, optionally filtered by a server's IP and port."""
            q = self._get_base_count_query(func.sum(ServerPlayerCount.count).label('v'))

            if ip and port:
                q = q.filter(ServerPlayerCount.ip == ip, ServerPlayerCount.port == port)

            return q.all()

        def get_server_count(self, active_only=False):
            """Return the online servers count, optionally filtered by the active ones only."""
            q = self._get_base_count_query(func.count('*').label('v'))

            if active_only:
                q = q.filter(ServerPlayerCount.count > 0)

            return q.all()

        def get_old_entries(self):
            """Return entries older than 1 weeks (exclusive)."""
            return self.filter(ServerPlayerCount.measured_at < one_week_ago()).all()

    __tablename__ = 'servers_player_count'
    __table_args__ = (db.Index('ip_port_idx', 'ip', 'port'), )
    query_class = ServerPlayerCountQuery

    ip = db.Column(db.String(15), nullable=False)
    port = db.Column(db.Integer, nullable=False)

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def server_players_data(ip=None, port=None):
        """Return the servers players chart data, optionally filtering by a server's IP and port."""
        return Measurable.transform_data(ServerPlayerCount.query.get_player_count(ip, port))

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def servers_data(active_only=False):
        """Return the servers chart data, optionally filtering by active servers only."""
        return Measurable.transform_data(ServerPlayerCount.query.get_server_count(active_only))

    def __repr__(self):
        return 'ServerPlayerCount:{}'.format(self.id)


class SteamPlayerCount(db.Model, Measurable):
    class SteamPlayerCountQuery(db.Query):
        def get_player_count(self):
            """Return the Steam players count."""
            q = self.with_entities(SteamPlayerCount.measured_at.label('t'), SteamPlayerCount.count.label('v'))
            q = q.filter(SteamPlayerCount.measured_at >= one_week_ago()).group_by('t')

            return q.all()

        def get_old_entries(self):
            """Return entries older than 1 weeks (exclusive)."""
            return self.filter(SteamPlayerCount.measured_at < one_week_ago()).all()

    __tablename__ = 'steam_players_count'
    query_class = SteamPlayerCountQuery

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def players_data():
        """Return the Steam players count chart data."""
        return Measurable.transform_data(SteamPlayerCount.query.get_player_count())

    def __repr__(self):
        return 'SteamPlayerCount:{}'.format(self.id)


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
    _value = db.Column('value', db.String(255))

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
    def delete(name):
        """Delete the given variable, if it exists."""
        var = Variable.query.filter(Variable.name == name).first()

        if var:
            db.session.remove(var)

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
                    peaks[name] = peaks[name].format('MMMM D, YYYY')

        return peaks

    def __repr__(self):
        return 'Variable:{}'.format(self.id)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    steam_id = db.Column(db.String(17), nullable=False, unique=True)
    username = db.Column(db.String(80), nullable=False)
    small_avatar_url = db.Column(db.String(255))
    large_avatar_url = db.Column(db.String(255))
    country_code = db.Column(db.String(2))
    is_profile_public = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), nullable=False)
    updated_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), onupdate=arrow.utcnow().floor('minute'), nullable=False)
    last_login_at = db.Column(ArrowType, nullable=False)

    rwr_accounts = db.relationship('RwrAccount', backref='user', lazy=True, foreign_keys='RwrAccount.user_id')

    def get_rwr_accounts_by_type(self, type):
        """Return the RwrAccounts linked to this user, filtered by account type."""
        return [rwr_account for rwr_account in self.rwr_accounts if rwr_account.type == RwrAccountType(type.upper())]

    @memoized_property
    def country_name(self):
        return iso3166.countries_by_alpha2.get(self.country_code.upper()).name if self.country_code else ''

    def get_link(self, absolute=False):
        def _get_link(self, absolute):
            return url_for('user_profile', user_id=self.id, slug=self.slug, _external=absolute)

        if current_app:
            link = _get_link(self, absolute=absolute)
        else:
            with app.app_context():
                link = _get_link(self, absolute=absolute)

        return link

    @memoized_property
    def link(self):
        """Return the link to this User profile page."""
        return self.get_link()

    @memoized_property
    def link_absolute(self):
        """Return the absolute link to this User profile page."""
        return self.get_link(absolute=True)

    @memoized_property
    def slug(self):
        return slugify(self.username)

    @staticmethod
    def get_by_steam_id(steam_id, create_if_unexisting=False):
        """Get a User according its Steam ID, optionally creating it if it doesn't exist."""
        user = User.query.filter(User.steam_id == steam_id).first()

        if not user and create_if_unexisting:
            user = User()
            user.steam_id = steam_id

        return user

    @memoized_property
    def has_rwr_accounts(self):
        """Determine is this User object have at least one RwrAccount."""
        return RwrAccount.query.with_entities(func.count('*')).filter(RwrAccount.user_id == self.id).scalar() > 0

    def __repr__(self):
        return 'User:{}'.format(self.id)


class MarketAdType(Enum):
    OFFER = 'OFFER'
    REQUEST = 'REQUEST'


class MarketAdStatus(Enum):
    ACTIVE = 'ACTIVE'
    CONCLUDED = 'CONCLUDED'
    CANCELLED = 'CANCELLED'


class MarketAd(db.Model):
    __tablename__ = 'market_ads'
    __table_args__ = (
        db.Index('type_status_idx', 'type', 'status'),
        db.Index('rwr_account_id_idx', 'rwr_account_id'),
        db.Index('created_at_idx', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    type = db.Column(db.Enum(MarketAdType), nullable=False)
    item_id = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.Enum(MarketAdStatus), nullable=False, default=MarketAdStatus.ACTIVE)
    created_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), nullable=False)
    updated_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), onupdate=arrow.utcnow().floor('minute'), nullable=False)

    rwr_account_id = db.Column(db.Integer, db.ForeignKey('rwr_accounts.id'), nullable=False)

    @memoized_property
    def total_price(self):
        return self.quantity * self.unit_price

    @memoized_property
    def total_price_display(self):
        return helpers.humanize_integer(self.total_price)

    @memoized_property
    def unit_price_display(self):
        return helpers.humanize_integer(self.unit_price)

    @memoized_property
    def is_free(self):
        return self.total_price == 0

    @memoized_property
    def type_for_url(self):
        if self.type == MarketAdType.OFFER:
            return 'offers'
        elif self.type == MarketAdType.REQUEST:
            return 'requests'
        else:
            return 'unknown'

    def get_link(self, absolute=False):
        def _get_link(self, absolute):
            return url_for('market_ad_details', ad_type=self.type_for_url, ad_id=self.id, _external=absolute)

        if current_app:
            link = _get_link(self, absolute=absolute)
        else:
            with app.app_context():
                link = _get_link(self, absolute=absolute)

        return link

    @memoized_property
    def link(self):
        """Return the link to this MarketAd page."""
        return self.get_link()

    @memoized_property
    def link_absolute(self):
        """Return the absolute link to this MarketAd page."""
        return self.get_link(absolute=True)

    @staticmethod
    def get_market_ad_list(type, status=MarketAdStatus.ACTIVE, page=None, limit=None):
        q = MarketAd.query.filter(
            MarketAd.type == type,
            MarketAd.status == status
        )

        q = q.order_by(MarketAd.created_at.desc())

        if page:
            return q.paginate(
                page=page,
                per_page=limit,
                error_out=False
            )
        elif limit:
            q = q.limit(limit)

        return q.all()


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
    updated_at = db.Column(ArrowType, default=arrow.utcnow().floor('minute'), onupdate=arrow.utcnow().floor('minute'), nullable=False)
    claim_possible_until = db.Column(ArrowType)
    claimed_at = db.Column(ArrowType)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    claim_initiated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    stats = db.relationship('RwrAccountStat', backref='rwr_account', lazy=True)
    market_ads = db.relationship('MarketAd', backref='rwr_account', lazy=True)

    @memoized_property
    def link(self):
        """Return the link to this Player details page."""
        def get_link(self):
            return url_for('player_details', database=self.type.value.lower(), username=self.username)

        if current_app:
            link = get_link(self)
        else:
            with app.app_context():
                link = get_link(self)

        return link

    @memoized_property
    def type_display(self):
        """The database name."""
        return rwr.utils.get_database_name(self.type.value.lower())

    @memoized_property
    def link(self):
        """Return the link to this Player details page."""
        def get_link(self):
            return url_for('player_details', database=self.type.value.lower(), username=self.username)

        if current_app:
            link = get_link(self)
        else:
            with app.app_context():
                link = get_link(self)

        return link

    @memoized_property
    def type_display(self):
        """The database name."""
        return rwr.utils.get_database_name(self.type.value.lower())

    @memoized_property
    def ordered_stats(self):
        """Return a query which have to be executed to get all RwrAccountStat linked to this RwrAccount."""
        return RwrAccountStat.query.filter(RwrAccountStat.rwr_account_id == self.id).order_by(RwrAccountStat.created_at.desc())

    @memoized_property
    def has_stats(self):
        """Determine is this RwrAccount object have at least one RwrAccountStat."""
        return RwrAccountStat.query.with_entities(func.count('*')).filter(RwrAccountStat.rwr_account_id == self.id).scalar() > 0

    @staticmethod
    def get_by_type_and_username(type, username, create_if_unexisting=False):
        """Return an RwrAccount given its type and username, optionally creating it if it doesn't exist."""
        type = RwrAccountType(type.upper())

        rwr_account = RwrAccount.query.filter(
            RwrAccount.type == type,
            RwrAccount.username == username
        ).first()

        if not rwr_account and create_if_unexisting:
            rwr_account = RwrAccount()
            rwr_account.type = type
            rwr_account.username = username

        return rwr_account

    def init_claim(self, user_id):
        """Initialize the claim procedure for this RwrAccount."""
        self.claim_initiated_by_user_id = user_id
        self.claim_possible_until = arrow.utcnow().floor('second').shift(minutes=+app.config['PLAYER_CLAIM_DELAY'])

    def reset_claim(self):
        """Reset the claim procedure for this RwrAccount."""
        self.claim_initiated_by_user_id = None
        self.claim_possible_until = None

    def claim(self, user_id):
        """Make a User claim this RwrAccount."""
        self.user_id = user_id
        self.claimed_at = arrow.utcnow().floor('minute')

        self.reset_claim()

    def has_claim_expired(self):
        """Determine if this RwrAccount claim period has expired."""
        if arrow.utcnow() >= self.claim_possible_until:
            self.reset_claim()

            return True

        return False

    def __repr__(self):
        return 'RwrAccount:{}'.format(self.id)


class RwrAccountStat(db.Model):
    __tablename__ = 'rwr_account_stats'
    __table_args__ = (
        db.Index('rwr_account_id_idx', 'rwr_account_id'),
        db.Index('created_at_idx', 'created_at'),
        db.Index('hash_idx', 'hash')
    )

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
    hash = db.Column(db.String(32), nullable=False)
    promoted_to_rank_id = db.Column(db.Integer)
    created_at = db.Column(ArrowType, default=arrow.utcnow().floor('day'), nullable=False)

    rwr_account_id = db.Column(db.Integer, db.ForeignKey('rwr_accounts.id'), nullable=False)

    def compute_hash(self):
        """Compute the hash corresponding to the data of this RwrAccountStat."""
        data = [
            self.leaderboard_position,
            self.xp,
            self.kills,
            self.deaths,
            self.time_played,
            self.longest_kill_streak,
            self.targets_destroyed,
            self.vehicles_destroyed,
            self.soldiers_healed,
            self.teamkills,
            self.distance_moved,
            self.shots_fired,
            self.throwables_thrown,
            self.rwr_account_id
        ]

        data = [str(d) for d in data]
        data = ':'.join(data).encode()

        self.hash = hashlib.md5(data).hexdigest()

    @staticmethod
    def transform_data(rows, column, format='YYYY-MM-DD'):
        """Given a list of RwrAccountStat, convert to a list exploitable to be displayed in a chart."""
        return [{
            't': row.created_at.format(format) if format else row.created_at,
            'v': getattr(row, column),
            'ptr': row.promoted_to_rank.name if row.promoted_to_rank else None
        } for row in rows]

    @staticmethod
    def get_stats_for_date(rwr_account_id, date):
        """Return the most recent RwrAccountStat for the given rwr_account_id and date (arrow instance)."""
        return RwrAccountStat.query.filter(
            RwrAccountStat.rwr_account_id == rwr_account_id,
            RwrAccountStat.created_at <= date.floor('day')
        ).order_by(RwrAccountStat.created_at.desc()).first()

    @staticmethod
    @cache.memoize(timeout=app.config['GRAPHS_DATA_CACHE_TIMEOUT'])
    def get_stats_for_column(rwr_account, column=None):
        """Return the player's score, K/D ratio and/or leaderboard position evolution data for the past year."""
        rwr_account_stats = RwrAccountStat.query.filter(
            RwrAccountStat.rwr_account_id == rwr_account.id,
            RwrAccountStat.created_at >= one_year_ago()
        ).order_by(RwrAccountStat.created_at.desc()).all()

        # Set RwrAccount relations now to prevent lazy loading issue (and to prevent extra DB query)
        for rwr_account_stat in rwr_account_stats:
            rwr_account_stat.rwr_account = rwr_account

        if not column:
            return {
                'ratio': RwrAccountStat.transform_data(rwr_account_stats, 'kd_ratio'),
                'score': RwrAccountStat.transform_data(rwr_account_stats, 'score'),
                'position': RwrAccountStat.transform_data(rwr_account_stats, 'leaderboard_position')
            }
        else:
            return RwrAccountStat.transform_data(rwr_account_stats, column, format=None)

    @memoized_property
    def promoted_to_rank(self):
        return rwr.utils.get_rank_object(self.rwr_account.type.value.lower(), self.promoted_to_rank_id) if self.promoted_to_rank_id else None

    @memoized_property
    def score(self):
        return self.kills - self.deaths

    @memoized_property
    def kd_ratio(self):
        return round(self.kills / self.deaths, 2) if self.deaths > 0 else 0.00

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
        return 'RwrAccountStat:{}'.format(self.id)
