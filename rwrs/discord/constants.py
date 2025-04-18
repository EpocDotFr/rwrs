from flask_discord_interactions import Permission
from rwrs import helpers
from enum import Enum
from app import app
import rwr.constants
import re

EVOLUTION_TYPES = {
    'ratio': {'name': 'K/D ratio', 'column': 'kd_ratio'},
    'score': {'name': 'Score', 'column': 'score'},
}

PLAYER_SORTS = {
    'score': {'name': 'score', 'value': rwr.constants.PlayersSort.SCORE.value, 'getter': lambda player: player.score_display},
    'xp': {'name': 'experience', 'value': rwr.constants.PlayersSort.XP.value, 'getter': lambda player: player.xp_display},
    'kills': {'name': 'kills', 'value': rwr.constants.PlayersSort.KILLS.value, 'getter': lambda player: player.kills_display},
    'deaths': {'name': 'deaths', 'value': rwr.constants.PlayersSort.DEATHS.value, 'getter': lambda player: player.deaths_display},
    'ratio': {'name': 'K/D ratio', 'value': rwr.constants.PlayersSort.KD_RATIO.value, 'getter': lambda player: str(player.kd_ratio)},
    'time': {'name': 'time played', 'value': rwr.constants.PlayersSort.TIME_PLAYED.value, 'getter': lambda player: helpers.humanize_seconds_to_hours(player.time_played)},
    'streak': {'name': 'longest kill streak', 'value': rwr.constants.PlayersSort.LONGEST_KILL_STREAK.value, 'getter': lambda player: player.longest_kill_streak_display},
    'tk': {'name': 'teamkills', 'value': rwr.constants.PlayersSort.TEAMKILLS.value, 'getter': lambda player: player.teamkills_display},
    'heals': {'name': 'soldiers healed', 'value': rwr.constants.PlayersSort.SOLDIERS_HEALED.value, 'getter': lambda player: player.soldiers_healed_display},
    'shots': {'name': 'shots fired', 'value': rwr.constants.PlayersSort.SHOTS_FIRED.value, 'getter': lambda player: player.shots_fired_display},
    'distance': {'name': 'distance moved (km)', 'value': rwr.constants.PlayersSort.DISTANCE_MOVED.value, 'getter': lambda player: str(player.distance_moved)},
    'throws': {'name': 'throwables thrown', 'value': rwr.constants.PlayersSort.THROWABLES_THROWN.value, 'getter': lambda player: player.throwables_thrown_display},
    'vehicles': {'name': 'vehicles destroyed', 'value': rwr.constants.PlayersSort.VEHICLES_DESTROYED.value, 'getter': lambda player: player.vehicles_destroyed_display},
    'targets': {'name': 'targets destroyed', 'value': rwr.constants.PlayersSort.TARGETS_DESTROYED.value, 'getter': lambda player: player.targets_destroyed_display},
}

DATABASE_CHOICES = Enum('DATABASE_CHOICES', {d: d for d in rwr.constants.VALID_DATABASES})
EVOLUTION_TYPE_CHOICES = Enum('EVOLUTION_TYPE_CHOICES', {d: d for d in EVOLUTION_TYPES.keys()})
SERVER_TYPE_CHOICES = Enum('SERVER_TYPE_CHOICES', {d: d for d in rwr.constants.VALID_SERVER_TYPES})
PLAYER_SORT_CHOICES = Enum('PLAYER_SORT_CHOICES', {d: d for d in PLAYER_SORTS.keys()})

DEFAULT_DATABASE = DATABASE_CHOICES.invasion
DEFAULT_PLAYER_SORT = PLAYER_SORT_CHOICES.score
PLAYERS_LIMIT = 24
SERVERS_LIMIT = 10
EMBED_COLOR = 10800919 # The well-known primary RWRS color #A4CF17, in the decimal format

PERMISSIONS = {
    'myself': Permission(user=app.config['MY_DISCORD_ID']),
}

TIME_AGO_REGEX = re.compile(r'(?P<days_ago>\d+) day(?:s?) ago|(?P<weeks_ago>\d+) week(?:s?) ago|(?P<months_ago>\d+) month(?:s?) ago|(?P<years_ago>\d+) year(?:s?) ago')

TEXT_COLOR = '#ffffff'
BG_COLOR_PRIMARY = '#3f3f3f'
BG_COLOR_SECONDARY = '#444444'
BORDER_COLOR = '#333333'
PRIMARY_COLOR = '#A4CF17'
SECONDARY_COLOR = '#44b2f8'

DATE_FORMATS = [
    'MMM D YYYY',
    'MMM DD YYYY',
    'MMM D, YYYY',
    'MMM DD, YYYY',
    'MMM D',
    'MMM DD',
    'MMMM D YYYY',
    'MMMM DD YYYY',
    'MMMM D, YYYY',
    'MMMM DD, YYYY',
    'MMMM D',
    'MMMM DD',
    'DD/MM/YYYY',
    'D/M/YYYY',
    'YYYY-M-D',
    'YYYY-MM-DD'
]
