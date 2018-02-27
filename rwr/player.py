from . import constants, utils
from flask import url_for
import math


class Player:
    playing_on_server = None

    @classmethod
    def load(cls, database, node, alternative=False):
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
        rank_image_cell = node[17]

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

        _, rank_id = utils.parse_rank_path(rank_image_cell[0].get('src'))

        if rank_id:
            ret.rank = ret.get_rank_object(int(rank_id), return_none=False)

        ret.next_rank = ret.get_next_rank()
        ret.xp_to_next_rank = ret.get_xp_to_next_rank()
        ret.xp_percent_completion_to_next_rank = ret.get_xp_percent_completion_to_next_rank()
        ret.unlocks = ret.get_unlocks()

        ret.link = url_for('player_details', database=ret.database, username=ret.username)

        return ret

    def set_playing_on_server(self, servers):
        """Determine if this user is playing on one of the given servers."""
        for server in servers:
            if not server.players.list:
                continue

            if self.username in server.players.list:
                self.playing_on_server = server

                return

    def get_next_rank(self):
        """Get the next rank of the player (if applicable)."""
        if self.rank.id is None:
            return None

        if self.rank.id == 16: # Highest rank already reached
            return False

        next_rank_id = self.rank.id + 1

        return self.get_rank_object(next_rank_id)

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

    def get_rank_object(self, rank_id, return_none=False):
        """Return a new PlayerRank object given a rank ID."""
        ret = PlayerRank()

        applicable_ranks = constants.RANKS[constants.PLAYERS_LIST_DATABASES[self.database]['ranks_country']]

        if str(rank_id) not in applicable_ranks:
            return None if return_none else ret

        ret.id = rank_id
        ret.name = applicable_ranks[str(rank_id)]['name']
        ret.xp = applicable_ranks[str(rank_id)]['xp']

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

    def __repr__(self):
        return 'Player:' + self.username


class PlayerRank:
    id = None
    name = None
    xp = 0

    def __repr__(self):
        return 'PlayerRank:' + self.id
