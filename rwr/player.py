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
    def load(cls, database, node, alternative=False):
        """Load a player data from an HTML <tr> node."""
        ret = cls()

        leaderboard_position_node = node[0]
        username_node = node[1]
        kills_node = node[2]
        deaths_node = node[3]
        score_node = node[4]
        kd_ratio_node = node[5]
        time_played_node = node[6]
        longest_kill_streak_node = node[8 if alternative else 7]
        targets_destroyed_node = node[9 if alternative else 8]
        vehicles_destroyed_node = node[10 if alternative else 9]
        soldiers_healed_node = node[11 if alternative else 10]
        teamkills_node = node[7 if alternative else 11]
        distance_moved_node = node[12]
        shots_fired_node = node[13]
        throwables_thrown_node = node[14]
        xp_node = node[15]

        ret.database = database

        ret.leaderboard_position = int(leaderboard_position_node.text)
        ret.username = username_node.text.encode('iso-8859-1').decode('utf-8')
        ret.kills = int(kills_node.text)
        ret.deaths = int(deaths_node.text)
        ret.score = int(score_node.text)
        ret.kd_ratio = float(kd_ratio_node.text)
        ret.time_played = utils.parse_time(time_played_node.text)
        ret.longest_kill_streak = int(longest_kill_streak_node.text)
        ret.targets_destroyed = int(targets_destroyed_node.text)
        ret.vehicles_destroyed = int(vehicles_destroyed_node.text)
        ret.soldiers_healed = int(soldiers_healed_node.text)
        ret.teamkills = int(teamkills_node.text)
        ret.distance_moved = float(distance_moved_node.text.replace('km', ''))
        ret.shots_fired = int(shots_fired_node.text)
        ret.throwables_thrown = int(throwables_thrown_node.text)
        ret.xp = int(xp_node.text)

        if current_app:
            ret.set_links()
        else:
            with app.app_context():
                ret.set_links()

        return ret

    @classmethod
    def craft(cls, rwr_account, rwr_account_stat):
        """Create player data from RwrAccount and RwrAccountStat instances."""
        ret = cls()

        ret.rwr_account = rwr_account

        ret.database = rwr_account.type.value.lower()

        ret.username = rwr_account.username.encode('iso-8859-1').decode('utf-8')

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

        if current_app:
            ret.set_links()
        else:
            with app.app_context():
                ret.set_links()

        return ret

    @memoized_property
    def leaderboard_position_display(self):
        return helpers.humanize_integer(self.leaderboard_position)

    @memoized_property
    def is_me(self):
        return self.username.lower() == app.config['MY_USERNAME']

    @memoized_property
    def is_contributor(self):
        return self.username.lower() in app.config['CONTRIBUTORS']

    @memoized_property
    def is_rwr_dev(self):
        return self.username.lower() in app.config['DEVS']

    @memoized_property
    def is_ranked_servers_admin(self):
        return self.username.lower() in app.config['RANKED_SERVERS_ADMINS']

    @memoized_property
    def username_display(self):
        return '{}{}{}'.format(
            self.username,
            ' :wave:' if self.is_me else ' :v:️' if self.is_contributor else ' :tools:' if self.is_rwr_dev else '',
            ' :scales:' if self.is_ranked_servers_admin else ''
        )

    @memoized_property
    def kills_display(self):
        return helpers.humanize_integer(self.kills)

    @memoized_property
    def deaths_display(self):
        return helpers.humanize_integer(self.deaths)

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

    @memoized_property
    def xp_display(self):
        return helpers.humanize_integer(self.xp)

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

    @memoized_property
    def display_time_played_in_days(self):
        return self.time_played > 60 * 60 * 24

    @memoized_property
    def database_name(self):
        return utils.get_database_name(self.database)

    @memoized_property
    def database_game_type(self):
        if self.database == 'invasion':
            return 'vanilla'
        else:
            return self.database

    @memoized_property
    def next_rank(self):
        """Next player rank (if applicable)."""
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

        return self._get_rank_object(next_rank_id)

    @memoized_property
    def rank(self):
        """Current player rank."""
        ranks = constants.RANKS[constants.PLAYERS_LIST_DATABASES[self.database]['ranks_country']]

        for rank_id, rank in ranks.items():
            if rank['xp'] > self.xp:
                break

            current_rank_id = rank_id

        return self._get_rank_object(int(current_rank_id))

    @memoized_property
    def xp_to_next_rank(self):
        """Amount of XP the player needs to be promoted to the next rank."""
        if not self.next_rank:
            return None

        return self.next_rank.xp - self.xp

    @memoized_property
    def xp_percent_completion_to_next_rank(self):
        """Percentage of XP the player obtained for the next rank."""
        if not self.next_rank:
            return None

        return round((self.xp * 100) / self.next_rank.xp, 2)

    def _get_rank_object(self, rank_id):
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

    @memoized_property
    def unlocks(self):
        """What the player unlocked (or not)."""
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
