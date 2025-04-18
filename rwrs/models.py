from sqlalchemy_utils import ArrowType, UUIDType
from sqlalchemy.util import memoized_property
from flask import url_for, current_app
from collections import OrderedDict
from flask_login import UserMixin
from app import db, cache, app
from sqlalchemy import func
from slugify import slugify
from rwrs import helpers
from enum import Enum
import rwr.utils
import hashlib
import iso3166
import arrow
import json
import uuid


def one_week_ago():
    """Return an Arrow object 1 week in the past."""
    return arrow.utcnow().floor('minute').shift(weeks=-1)


def one_year_ago():
    """Return an Arrow object 1 year in the past."""
    return arrow.utcnow().floor('day').shift(years=-1)


class Measurable:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # TODO To remove because useless and non-efficient

    measured_at = db.Column(ArrowType, default=lambda: arrow.utcnow().floor('minute'), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    @staticmethod
    def transform_data(rows, format='YYYY-MM-DDTHH:mm:ss', value=lambda v: int(v)):
        """Given a list of date => number, convert the date to a string format."""
        return [{'t': row[0].format(format), 'v': value(row[1])} for row in rows]


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
    JSON = 'JSON'


class Variable(db.Model):
    __tablename__ = 'variables'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.Enum(VariableType), nullable=False)
    _value = db.Column('value', db.Text)

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
            elif self.type == VariableType.JSON:
                return json.loads(self._value, object_pairs_hook=OrderedDict)
            else:
                raise ValueError('Unhandled value type')

        return self._value

    @value.setter
    def value(self, value):
        """Set the value an d type of this Variable."""
        if value and not isinstance(value, str):
            if isinstance(value, int):
                self.type = VariableType.INTEGER
                self._value = str(value)
            elif isinstance(value, float):
                self.type = VariableType.FLOAT
                self._value = str(value)
            elif isinstance(value, bool):
                self.type = VariableType.BOOL
                self._value = str(int(value))
            elif isinstance(value, arrow.Arrow):
                self.type = VariableType.ARROW
                self._value = value.format()
            elif isinstance(value, dict):
                self.type = VariableType.JSON
                self._value = json.dumps(value)
            else:
                raise ValueError('Unhandled value type')
        else:
            self.type = VariableType.STRING
            self._value = value

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
            db.session.delete(var)

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

    @staticmethod
    def set_event(name, datetime, server_ip_and_port):
        """Sets the next RWR event."""
        arrow.get(datetime, app.config['EVENT_DATETIME_STORAGE_FORMAT']) # Just to validate

        Variable.set_value('event', {
            'name': name,
            'datetime': datetime,
            'server_ip_and_port': server_ip_and_port
        })

    @staticmethod
    def get_event(with_server=True):
        """Gets the next RWR event (if any)."""
        event = Variable.get_value('event')

        if not event:
            return None

        event_datetime = arrow.get(event['datetime'], app.config['EVENT_DATETIME_STORAGE_FORMAT']).floor('minute')
        now_in_event_timezone = arrow.now(event_datetime.tzinfo).floor('minute')

        if now_in_event_timezone >= event_datetime.shift(hours=+5):
            return None

        event['datetime'] = event_datetime
        event['is_ongoing'] = now_in_event_timezone >= event_datetime
        event['display_server_players_count'] = now_in_event_timezone >= event_datetime.shift(minutes=-15)
        event['server'] = rwr.scraper.get_server_by_ip_and_port(event['server_ip_and_port']) if with_server and event['server_ip_and_port'] else None

        return event

    def __repr__(self):
        return 'Variable:{}'.format(self.id)


class UserFriend(db.Model):
    __tablename__ = 'user_friends'
    __table_args__ = (db.Index('user_id_idx', 'user_id'), db.Index('user_id_username_idx', 'user_id', 'username', unique=True))

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    username = db.Column(db.String(16), nullable=False)
    created_at = db.Column(ArrowType, default=lambda: arrow.utcnow().floor('minute'), nullable=False)

    @memoized_property
    def playing_on_server(self):
        """Return the server this friend is currently playing on."""
        servers = rwr.scraper.get_servers()

        for server in servers:
            if not server.players.list:
                continue

            if self.username in server.players.list:
                return server

        return None

    def get_link(self, absolute=False):
        if not self.database:
            return None

        def _get_link(self, absolute):
            params = {
                'database': self.database,
                'username': self.username
            }

            return url_for('player_details', **params, _external=absolute)

        if current_app:
            link = _get_link(self, absolute=absolute)
        else:
            with app.app_context():
                link = _get_link(self, absolute=absolute)

        return link

    @memoized_property
    def link(self):
        """Return the link to the Player profile page of this Friend."""
        return self.get_link()

    @memoized_property
    def link_absolute(self):
        """Return the absolute link to the Player profile page of this Friend."""
        return self.get_link(absolute=True)

    @memoized_property
    def database(self):
        return self.playing_on_server.database if self.playing_on_server else None

    @memoized_property
    def database_name(self):
        return rwr.utils.get_database_name(self.database) if self.database else None

    @memoized_property
    def is_myself(self):
        return helpers.is_player_myself(self.username)

    @memoized_property
    def is_contributor(self):
        return helpers.is_player_contributor(self.username)

    @memoized_property
    def is_rwr_dev(self):
        return helpers.is_player_rwr_dev(self.username)

    @memoized_property
    def is_official_servers_mod(self):
        return helpers.is_player_official_server_mod(self.username)

    def __repr__(self):
        return 'UserFriend:{}'.format(self.id)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = (db.Index('pat_idx', 'pat', unique=True), )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    steam_id = db.Column(db.String(17), nullable=False, unique=True)
    username = db.Column(db.String(80), nullable=False)
    small_avatar_url = db.Column(db.String(255))
    large_avatar_url = db.Column(db.String(255))
    country_code = db.Column(db.String(2))
    is_profile_public = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(ArrowType, default=lambda: arrow.utcnow().floor('minute'), nullable=False)
    updated_at = db.Column(ArrowType, default=lambda: arrow.utcnow().floor('minute'), onupdate=lambda: arrow.utcnow().floor('minute'), nullable=False)
    last_login_at = db.Column(ArrowType, nullable=False)
    pat = db.Column(UUIDType, default=lambda: uuid.uuid4())
    is_forbidden_to_access_api = db.Column(db.Boolean, nullable=False, default=False)
    api_last_called_at = db.Column(ArrowType)

    rwr_accounts = db.relationship('RwrAccount', backref='user', lazy=True, foreign_keys='RwrAccount.user_id')
    friends = db.relationship('UserFriend', backref='user', lazy=True, foreign_keys='UserFriend.user_id')

    def sync_rwr_accounts(self, only_this_database=None):
        """Synchronize all RWR accounts owned by this user with the official players list."""
        if not app.config['RWR_ACCOUNTS_BY_STEAM_ID_ENDPOINT']:
            return

        players = rwr.scraper.get_players_by_steam_id(self.steam_id, only_this_database)

        if not players:
            return

        for database, usernames in players.items():
            if usernames:
                scraper_rwr_accounts = RwrAccount.get_many_by_type_and_usernames(database, usernames, create_if_unexisting=True)

                for scraper_rwr_account in scraper_rwr_accounts:
                    if scraper_rwr_account.user_id == self.id:
                        continue

                    scraper_rwr_account.user = self

                    db.session.add(scraper_rwr_account)

            for user_rwr_account in self.get_rwr_accounts_by_type(database):
                if user_rwr_account.username in usernames:
                    continue

                RwrAccountStat.query.filter(RwrAccountStat.rwr_account_id == user_rwr_account.id).delete()

                db.session.delete(user_rwr_account)

    def get_rwr_accounts_by_type(self, type):
        """Return the RwrAccounts linked to this user, filtered by account type."""
        return [rwr_account for rwr_account in self.rwr_accounts if rwr_account.type == RwrAccountType(type.upper())]

    @memoized_property
    def is_rwrs_admin(self):
        return self.steam_id in app.config['ADMINS']

    @memoized_property
    def country_name(self):
        return iso3166.countries_by_alpha2.get(self.country_code.upper()).name if self.country_code else ''

    def get_link(self, absolute=False):
        def _get_link(self, absolute):
            params = {
                'user_id': self.id,
                'slug': self.slug
            }

            return url_for('user_profile', **params, _external=absolute)

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

    def get_country_flag(self, absolute=False):
        if not self.country_code:
            return None

        def _get_country_flag(self, absolute):
            params = {
                'country_code': self.country_code.upper(),
            }

            flag_url = 'images/flags/{country_code}.png'.format(**params)

            return url_for('static', filename=flag_url, _external=absolute)

        if current_app:
            link = _get_country_flag(self, absolute=absolute)
        else:
            with app.app_context():
                link = _get_country_flag(self, absolute=absolute)

        return link

    @memoized_property
    def country_flag(self):
        """Return the URL to this User country flag image."""
        return self.get_country_flag()

    @memoized_property
    def country_flag_absolute(self):
        """Return the absolute URL to this User country flag image."""
        return self.get_country_flag(absolute=True)

    @memoized_property
    def slug(self):
        return slugify(self.username)

    @memoized_property
    def steam_profile_url(self):
        return 'https://steamcommunity.com/profiles/{}'.format(self.steam_id)

    @staticmethod
    def get_by_steam_id(steam_id, create_if_unexisting=False):
        """Get a User according its Steam ID, optionally creating it if it doesn't exist."""
        user_was_created = False
        user = User.query.filter(User.steam_id == steam_id).first()

        if not user and create_if_unexisting:
            user = User()
            user.steam_id = steam_id

            user_was_created = True

        return user, user_was_created

    @staticmethod
    def get_by_pat(pat):
        """Get a User according its Personal Access Token."""
        return User.query.filter(User.pat == uuid.UUID(pat)).first()

    @memoized_property
    def has_rwr_accounts(self):
        """Determine is this User object have at least one RwrAccount."""
        return RwrAccount.query.with_entities(func.count('*')).filter(RwrAccount.user_id == self.id).scalar() > 0

    @memoized_property
    def friends_ordered_by_username(self):
        """Get the Friends of this User, ordered by username."""
        return UserFriend.query.filter(
            UserFriend.user_id == self.id
        ).order_by(UserFriend.username.asc()).all()

    @memoized_property
    def friends_divided_by_status(self):
        """"Get the Friends of this User divided in two lists: playing and non-playing friends."""
        playing_friends = [friend for friend in self.friends_ordered_by_username if friend.playing_on_server]
        non_playing_friends = [friend for friend in self.friends_ordered_by_username if not friend.playing_on_server]

        return playing_friends, non_playing_friends

    @memoized_property
    def number_of_playing_friends(self):
        """Return the number of Friends that are playing for this User."""
        return len([friend for friend in self.friends_ordered_by_username if friend.playing_on_server])

    def add_friend(self, username):
        """Add a friend to this User's friends list. Commiting DB operation is needed after calling this method."""
        user_friend = UserFriend()
        user_friend.user = self
        user_friend.username = username

        db.session.add(user_friend)

        return user_friend

    def add_friends(self, usernames):
        """Add multiple friends to this User's friends list in one go. Commiting DB operation is needed after calling this method."""
        existing_user_friends = UserFriend.query.filter(
            UserFriend.user_id == self.id,
            UserFriend.username.in_(usernames)
        ).all()

        existing_usernames = [existing_user_friend.username for existing_user_friend in existing_user_friends]

        usernames = [username.upper() for username in usernames if username not in existing_usernames]

        user_friends = []

        for username in usernames:
            user_friend = UserFriend()
            user_friend.user = self
            user_friend.username = username

            user_friends.append(user_friend)

        db.session.bulk_save_objects(user_friends)

        return user_friends

    def has_friend(self, username):
        """Determine if the given username is in the User's friends list."""
        return username in [friend.username for friend in self.friends_ordered_by_username]

    def get_friend(self, username):
        """Return the Friend with the given username in this User's friends list."""
        return UserFriend.query.filter(
            UserFriend.user_id == self.id,
            UserFriend.username == username
        ).first()

    def remove_friend(self, username):
        """Remove the given Friend from this User's friends list. Commiting DB operation is needed after calling this method."""
        user_friend = self.get_friend(username)

        if user_friend:
            db.session.delete(user_friend)

            return True
        else:
            return False

    def owns_rwr_account(self, rwr_account):
        """Determine if the given RWR account is owned by this user, without making DB queries."""
        return self.id == rwr_account.user_id

    def __repr__(self):
        return 'User:{}'.format(self.id)


class RwrAccountType(Enum):
    INVASION = 'INVASION'
    PACIFIC = 'PACIFIC'


class RwrAccount(db.Model):
    __tablename__ = 'rwr_accounts'
    __table_args__ = (db.Index('type_username_idx', 'type', 'username'), )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    type = db.Column(db.Enum(RwrAccountType), nullable=False)
    username = db.Column(db.String(16), nullable=False)
    pending_delete = db.Column(db.Boolean, nullable=False, default=False)
    last_seen_at = db.Column(ArrowType)
    created_at = db.Column(ArrowType, default=lambda: arrow.utcnow().floor('minute'), nullable=False)
    updated_at = db.Column(ArrowType, default=lambda: arrow.utcnow().floor('minute'), onupdate=lambda: arrow.utcnow().floor('minute'), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    stats = db.relationship('RwrAccountStat', backref='rwr_account', lazy=True)

    def get_link(self, absolute=False):
        def _get_link(self, absolute):
            params = {
                'database': self.database,
                'username': self.username
            }

            return url_for('player_details', **params, _external=absolute)

        if current_app:
            link = _get_link(self, absolute=absolute)
        else:
            with app.app_context():
                link = _get_link(self, absolute=absolute)

        return link

    @memoized_property
    def link(self):
        """Return the link to this Player profile page."""
        return self.get_link()

    @memoized_property
    def link_absolute(self):
        """Return the absolute link to this Player profile page."""
        return self.get_link(absolute=True)

    @memoized_property
    def type_display(self):
        """The database name."""
        return rwr.utils.get_database_name(self.database)

    @memoized_property
    def is_myself(self):
        return helpers.is_player_myself(self.username)

    @memoized_property
    def is_contributor(self):
        return helpers.is_player_contributor(self.username)

    @memoized_property
    def is_rwr_dev(self):
        return helpers.is_player_rwr_dev(self.username)

    @memoized_property
    def is_official_servers_mod(self):
        return helpers.is_player_official_server_mod(self.username)

    @memoized_property
    def database(self):
        return self.type.value.lower()

    @memoized_property
    def database_name(self):
        return self.type_display

    @memoized_property
    def ordered_stats(self):
        """Return a query which have to be executed to get all RwrAccountStat linked to this RwrAccount."""
        return RwrAccountStat.query.filter(RwrAccountStat.rwr_account_id == self.id).order_by(RwrAccountStat.created_at.desc())

    @memoized_property
    def has_stats(self):
        """Determine is this RwrAccount object have at least one RwrAccountStat."""
        return RwrAccountStat.query.with_entities(func.count('*')).filter(RwrAccountStat.rwr_account_id == self.id).scalar() > 0

    @memoized_property
    def hash(self):
        """Return the hashed representation of this account's username."""
        ret = 5381

        for x in self.username:
            ret = (((ret << 5) + ret) + ord(x)) & 0xFFFFFFFF

        return ret

    @memoized_property
    def realm(self):
        """Return the official server realm this account is owned by."""
        return rwr.constants.PLAYERS_LIST_DATABASES[self.database]['realm']

    @staticmethod
    def get_one_by_type_and_username(type, username, create_if_unexisting=False):
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

    @staticmethod
    def get_many_by_type_and_usernames(type, usernames, create_if_unexisting=False):
        """Return all RwrAccount matching the given type and usernames, optionally creating them if they doesn't exist."""
        type = RwrAccountType(type.upper())

        rwr_accounts = RwrAccount.query.filter(
            RwrAccount.type == type,
            RwrAccount.username.in_(usernames)
        ).all()

        if create_if_unexisting:
            rwr_accounts_usernames = [rwr_account.username for rwr_account in rwr_accounts]

            for username in usernames:
                if username in rwr_accounts_usernames:
                    continue

                rwr_account = RwrAccount()
                rwr_account.type = type
                rwr_account.username = username

                rwr_accounts.append(rwr_account)

        return rwr_accounts

    def __repr__(self):
        return 'RwrAccount:{}'.format(self.id)


class RwrAccountStat(db.Model):
    __tablename__ = 'rwr_account_stats'
    __table_args__ = (
        db.Index('rwr_account_id_idx', 'rwr_account_id'),
        db.Index('created_at_idx', 'created_at')
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

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
    created_at = db.Column(ArrowType, default=lambda: arrow.utcnow().floor('day'), nullable=False)

    rwr_account_id = db.Column(db.Integer, db.ForeignKey('rwr_accounts.id'), nullable=False)

    def compute_hash(self):
        """Compute the hash corresponding to the data of this RwrAccountStat."""
        data = [
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
        """Return the player's score or K/D ratio evolution data."""
        rwr_account_stats = RwrAccountStat.query.filter(
            RwrAccountStat.rwr_account_id == rwr_account.id
        ).order_by(RwrAccountStat.created_at.desc()).all()

        # Set RwrAccount relations now to prevent lazy loading issue (and to prevent extra DB query)
        for rwr_account_stat in rwr_account_stats:
            rwr_account_stat.rwr_account = rwr_account

        if not column:
            return {
                'ratio': RwrAccountStat.transform_data(rwr_account_stats, 'kd_ratio'),
                'score': RwrAccountStat.transform_data(rwr_account_stats, 'score'),
            }
        else:
            return RwrAccountStat.transform_data(rwr_account_stats, column, format=None)

    @memoized_property
    def promoted_to_rank(self):
        return rwr.utils.get_rank_object(self.rwr_account.database, self.promoted_to_rank_id) if self.promoted_to_rank_id else None

    @memoized_property
    def score(self):
        return self.kills - self.deaths

    @memoized_property
    def kd_ratio(self):
        return round(self.kills / self.deaths, 2) if self.deaths > 0 else 0.00

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
