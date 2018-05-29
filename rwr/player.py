from models import RwrAccount, RwrAccountType
from sqlalchemy.util import memoized_property
from flask import url_for, current_app
from . import constants, utils
from rwrs import app
import helpers
import math


class Player:
    playing_on_server = None

    @classmethod
    def load(cls, database, node, alternative=False, basic=False):
        """Load a player data from an HTML <tr> node."""
        ret = cls()

        position_cell = node[0]
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

        ret.position = int(position_cell.text)
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

        ret.database = database
        ret.database_name = utils.get_database_name(ret.database)
        ret.database_game_type = ret.get_game_type_from_database()

        if not basic:
            ret.rank = ret.get_current_rank()

            ret.position_display = helpers.humanize_integer(ret.position)

            username_lower = ret.username.lower()

            ret.is_me = username_lower == app.config['MY_USERNAME']
            ret.is_contributor = username_lower in app.config['CONTRIBUTORS']
            ret.is_rwr_dev = username_lower in app.config['DEVS']

            ret.username_display = '{}{}'.format(
                ret.username,
                ' 👋' if ret.is_me else ' ✌️' if ret.is_contributor else ' 🛠' if ret.is_rwr_dev else ''
            )

            ret.kills_display = helpers.humanize_integer(ret.kills)
            ret.deaths_display = helpers.humanize_integer(ret.deaths)
            ret.score_display = helpers.humanize_integer(ret.score)
            ret.longest_kill_streak_display = helpers.humanize_integer(ret.longest_kill_streak)
            ret.targets_destroyed_display = helpers.humanize_integer(ret.targets_destroyed)
            ret.vehicles_destroyed_display = helpers.humanize_integer(ret.vehicles_destroyed)
            ret.soldiers_healed_display = helpers.humanize_integer(ret.soldiers_healed)
            ret.teamkills_display = helpers.humanize_integer(ret.teamkills)
            ret.shots_fired_display = helpers.humanize_integer(ret.shots_fired)
            ret.throwables_thrown_display = helpers.humanize_integer(ret.throwables_thrown)
            ret.xp_display = helpers.humanize_integer(ret.xp)
            ret.display_time_played_in_days = ret.time_played > 60 * 60 * 24
            ret.next_rank = ret.get_next_rank()
            ret.xp_to_next_rank = ret.get_xp_to_next_rank()
            ret.xp_percent_completion_to_next_rank = ret.get_xp_percent_completion_to_next_rank()
            ret.unlocks = ret.get_unlocks()

            if current_app:
                ret.set_links()
            else:
                with app.app_context():
                    ret.set_links()

        return ret

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

    @memoized_property
    def rwr_account(self):
        """Return the RwrAccount associated to this Player."""
        return RwrAccount.query.filter(
            RwrAccount.type == RwrAccountType(self.database.upper()),
            RwrAccount.username == self.username
        ).first()

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
