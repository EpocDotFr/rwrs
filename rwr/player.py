from sqlalchemy.util import memoized_property
from flask import url_for, current_app
from . import constants, utils
from models import RwrAccount
from rwrs import app
import helpers
import math


class Player:
    playing_on_server = None
    _rwr_account = None

    @classmethod
    def load(cls, database, node, alternative=False, basic=False):
        """Load a player data from an HTML <tr> node."""
        ret = cls()

        leaderboard_position_cell = node[0]
        username_cell = node[1]
        kills_cell = node[2]
        deaths_cell = node[3]
        score_cell = node[4]
        kd_ratio_cell = node[5]
        time_played_cell = node[6]
        longest_kill_streak_cell = node[8 if alternative else 7]
        targets_destroyed_cell = node[9 if alternative else 8]
        vehicles_destroyed_cell = node[10 if alternative else 9]
        soldiers_healed_cell = node[11 if alternative else 10]
        teamkills_cell = node[7 if alternative else 11]
        distance_moved_cell = node[12]
        shots_fired_cell = node[13]
        throwables_thrown_cell = node[14]
        xp_cell = node[15]

        ret.database = database
        ret.database_name = utils.get_database_name(ret.database)
        ret.database_game_type = ret.get_game_type_from_database()

        ret.leaderboard_position = int(leaderboard_position_cell.text)
        ret.username = username_cell.text
        ret.kills = int(kills_cell.text)
        ret.deaths = int(deaths_cell.text)
        ret.score = int(score_cell.text)
        ret.kd_ratio = float(kd_ratio_cell.text)
        ret.time_played = utils.parse_time(time_played_cell.text)
        ret.longest_kill_streak = int(longest_kill_streak_cell.text)
        ret.targets_destroyed = int(targets_destroyed_cell.text)
        ret.vehicles_destroyed = int(vehicles_destroyed_cell.text)
        ret.soldiers_healed = int(soldiers_healed_cell.text)
        ret.teamkills = int(teamkills_cell.text)
        ret.distance_moved = float(distance_moved_cell.text.replace('km', ''))
        ret.shots_fired = int(shots_fired_cell.text)
        ret.throwables_thrown = int(throwables_thrown_cell.text)
        ret.xp = int(xp_cell.text)

        if not basic:
            ret.set_advanced_data()

        return ret

    @classmethod
    def craft(cls, rwr_account, rwr_account_stat):
        """Create player data from RwrAccount and RwrAccountStat instances."""
        ret = cls()

        ret.rwr_account = rwr_account

        ret.database = rwr_account.type.value.lower()
        ret.database_name = utils.get_database_name(ret.database)
        ret.database_game_type = ret.get_game_type_from_database()

        ret.username = rwr_account.username

        ret.leaderboard_position = rwr_account_stat.leaderboard_position
        ret.kills = rwr_account_stat.kills
        ret.deaths = rwr_account_stat.deaths
        ret.score = rwr_account_stat.score
        ret.kd_ratio = rwr_account_stat.kd_ratio
        ret.time_played = rwr_account_stat.time_played
        ret.longest_kill_streak = rwr_account_stat.longest_kill_streak
        ret.targets_destroyed = rwr_account_stat.targets_destroyed
        ret.vehicles_destroyed = rwr_account_stat.vehicles_destroyed
        ret.soldiers_healed = rwr_account_stat.soldiers_healed
        ret.teamkills = rwr_account_stat.teamkills
        ret.distance_moved = rwr_account_stat.distance_moved
        ret.shots_fired = rwr_account_stat.shots_fired
        ret.throwables_thrown = rwr_account_stat.throwables_thrown
        ret.xp = rwr_account_stat.xp

        ret.set_advanced_data()

        return ret

    def set_advanced_data(self):
        self.rank = self.get_current_rank()

        self.leaderboard_position_display = helpers.humanize_integer(self.leaderboard_position)

        username_lower = self.username.lower()

        self.is_me = username_lower == app.config['MY_USERNAME']
        self.is_contributor = username_lower in app.config['CONTRIBUTORS']
        self.is_rwr_dev = username_lower in app.config['DEVS']

        self.username_display = '{}{}'.format(
            self.username,
            ' 👋' if self.is_me else ' ✌️' if self.is_contributor else ' 🛠' if self.is_rwr_dev else ''
        )

        self.kills_display = helpers.humanize_integer(self.kills)
        self.deaths_display = helpers.humanize_integer(self.deaths)
        self.score_display = helpers.humanize_integer(self.score)
        self.longest_kill_streak_display = helpers.humanize_integer(self.longest_kill_streak)
        self.targets_destroyed_display = helpers.humanize_integer(self.targets_destroyed)
        self.vehicles_destroyed_display = helpers.humanize_integer(self.vehicles_destroyed)
        self.soldiers_healed_display = helpers.humanize_integer(self.soldiers_healed)
        self.teamkills_display = helpers.humanize_integer(self.teamkills)
        self.shots_fired_display = helpers.humanize_integer(self.shots_fired)
        self.throwables_thrown_display = helpers.humanize_integer(self.throwables_thrown)
        self.xp_display = helpers.humanize_integer(self.xp)
        self.display_time_played_in_days = self.time_played > 60 * 60 * 24
        self.next_rank = self.get_next_rank()
        self.xp_to_next_rank = self.get_xp_to_next_rank()
        self.xp_percent_completion_to_next_rank = self.get_xp_percent_completion_to_next_rank()
        self.unlocks = self.get_unlocks()

        if current_app:
            self.set_links()
        else:
            with app.app_context():
                self.set_links()

    def set_links(self):
        """Set the relative and absolute URLs of this player's details page."""
        params = {
            'database': self.database,
            'username': self.username
        }

        self.link = url_for('player_details', **params)
        self.link_absolute = url_for('player_details', **params, _external=True)

    def set_playing_on_server(self, servers):
        """Determine if this user is playing on one of the given servers."""
        for server in servers:
            if not server.players.list:
                continue

            if self.username in server.players.list:
                self.playing_on_server = server

                return

    def get_next_rank(self):
        """Return the next rank of the player (if applicable)."""
        if self.rank.id is None:
            return None

        ranks_country = constants.PLAYERS_LIST_DATABASES[self.database]['ranks_country']

        rank_ids = [int(rank_id) for rank_id in constants.RANKS[ranks_country].keys()]

        if self.database == 'pacific' and ranks_country == 'us': # The President rank for USMC isn't available in Pacific
            rank_ids = rank_ids[:-1]

        highest_rank_id = max(rank_ids)

        if self.rank.id == highest_rank_id: # Highest rank already reached
            return False

        next_rank_id = self.rank.id + 1

        return self.get_rank_object(next_rank_id)

    def get_current_rank(self):
        """Return the current rank of the player."""
        ranks = constants.RANKS[constants.PLAYERS_LIST_DATABASES[self.database]['ranks_country']]

        for rank_id, rank in ranks.items():
            if rank['xp'] > self.xp:
                break

            current_rank_id = rank_id

        return self.get_rank_object(int(current_rank_id))

    def get_xp_to_next_rank(self):
        """Return the amount of XP the player needs to be promoted to the next rank."""
        if not self.next_rank:
            return None

        return self.next_rank.xp - self.xp

    def get_xp_percent_completion_to_next_rank(self):
        """Return the percentage of XP the player obtained for the next rank."""
        if not self.next_rank:
            return None

        return round((self.xp * 100) / self.next_rank.xp, 2)

    def get_rank_object(self, rank_id):
        """Return a new PlayerRank object given a rank ID."""
        ret = PlayerRank()

        ranks = constants.RANKS[constants.PLAYERS_LIST_DATABASES[self.database]['ranks_country']]

        if str(rank_id) not in ranks:
            return ret

        ret.id = rank_id
        ret.name = ranks[str(rank_id)]['name']
        ret.xp = ranks[str(rank_id)]['xp']

        if current_app:
            ret.set_images_and_icons(self.database)
        else:
            with app.app_context():
                ret.set_images_and_icons(self.database)

        return ret

    def get_game_type_from_database(self):
        """Return the game type from this player's database name."""
        if self.database == 'invasion':
            return 'vanilla'
        else:
            return self.database

    def get_unlocks(self):
        """Compute what the player unlocked (or not)."""
        def _init_unlockable(ret, type):
            ret[type] = {
                'list': [],
                'current': 0,
                'max': len([un for required_xp, unlocks in constants.UNLOCKABLES[self.database_game_type].items() for unlock_id, unlock in unlocks.items() if unlock_id == type for un in unlock])
            }

        def _compute_unlockable(unlocks, ret, type):
            if type in unlocks:
                for unlockable in unlocks[type]:
                    unlocked = self.xp >= required_xp

                    unlockable['required_xp'] = required_xp
                    unlockable['unlocked'] = unlocked

                    if unlocked:
                        ret[type]['current'] += 1

                    ret[type]['list'].append(unlockable)

        ret = {
            'squad_mates': {
                'current': math.floor(self.xp / constants.SQUADMATES_STEPS_XP) if self.xp < constants.MAX_SQUADMATES * constants.SQUADMATES_STEPS_XP else constants.MAX_SQUADMATES,
                'xp_steps': constants.SQUADMATES_STEPS_XP,
                'max': constants.MAX_SQUADMATES
            }
        }

        _init_unlockable(ret, 'radio_calls')
        _init_unlockable(ret, 'weapons')
        _init_unlockable(ret, 'equipment')
        _init_unlockable(ret, 'throwables')

        for required_xp, unlocks in constants.UNLOCKABLES[self.database_game_type].items():
            _compute_unlockable(unlocks, ret, 'radio_calls')
            _compute_unlockable(unlocks, ret, 'weapons')
            _compute_unlockable(unlocks, ret, 'equipment')
            _compute_unlockable(unlocks, ret, 'throwables')

        return ret

    @property
    def rwr_account(self):
        """Return the RwrAccount associated to this Player."""
        return RwrAccount.get_by_type_and_username(self.database, self.username) if not self._rwr_account else self._rwr_account

    @rwr_account.setter
    def rwr_account(self, rwr_account):
        """Set the RwrAccount associated to this Player."""
        self._rwr_account = rwr_account

    @memoized_property
    def has_stats(self):
        """Determine if this Player has a RwrAccount and at least one persisted RwrAccountStat."""
        return self.rwr_account and self.rwr_account.has_stats

    def __repr__(self):
        return 'Player:' + self.username


class PlayerRank:
    id = None
    name = None
    xp = 0

    def __repr__(self):
        return 'PlayerRank:' + self.id

    def set_images_and_icons(self, database):
        """Set the relative and absolute URLs to the images and icon of this rank."""
        params = {
            'ranks_country': constants.PLAYERS_LIST_DATABASES[database]['ranks_country'],
            'rank_id': self.id
        }

        image_url = 'images/ranks/{ranks_country}/{rank_id}.png'.format(**params)
        icon_url = 'images/ranks/{ranks_country}/{rank_id}_icon.png'.format(**params)

        self.image = url_for('static', filename=image_url)
        self.image_absolute = url_for('static', filename=image_url, _external=True)

        self.icon = url_for('static', filename=icon_url)
        self.icon_absolute = url_for('static', filename=icon_url, _external=True)
