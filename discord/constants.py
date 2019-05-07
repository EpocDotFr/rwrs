from collections import OrderedDict
import rwr.constants
import helpers

VALID_PLAYER_SORTS = {
    'score': {'name': 'score', 'value': rwr.constants.PlayersSort.SCORE.value, 'getter': lambda player: player.score_display},
    'xp': {'name': 'experience', 'value': rwr.constants.PlayersSort.XP.value, 'getter': lambda player: player.xp_display},
    'kills': {'name': 'kills', 'value': rwr.constants.PlayersSort.KILLS.value, 'getter': lambda player: player.kills_display},
    'deaths': {'name': 'deaths', 'value': rwr.constants.PlayersSort.DEATHS.value, 'getter': lambda player: player.deaths_display},
    'ratio': {'name': 'K/D ratio', 'value': rwr.constants.PlayersSort.KD_RATIO.value, 'getter': lambda player: player.kd_ratio},
    'time': {'name': 'time played', 'value': rwr.constants.PlayersSort.TIME_PLAYED.value, 'getter': lambda player: helpers.humanize_seconds_to_hours(player.time_played)},
    'streak': {'name': 'longest kill streak', 'value': rwr.constants.PlayersSort.LONGEST_KILL_STREAK.value, 'getter': lambda player: player.longest_kill_streak_display},
    'tk': {'name': 'teamkills', 'value': rwr.constants.PlayersSort.TEAMKILLS.value, 'getter': lambda player: player.teamkills_display},
    'heals': {'name': 'soldiers healed', 'value': rwr.constants.PlayersSort.SOLDIERS_HEALED.value, 'getter': lambda player: player.soldiers_healed_display},
    'shots': {'name': 'shots fired', 'value': rwr.constants.PlayersSort.SHOTS_FIRED.value, 'getter': lambda player: player.shots_fired_display},
    'distance': {'name': 'distance moved (km)', 'value': rwr.constants.PlayersSort.DISTANCE_MOVED.value, 'getter': lambda player: player.distance_moved},
    'throws': {'name': 'throwables thrown', 'value': rwr.constants.PlayersSort.THROWABLES_THROWN.value, 'getter': lambda player: player.throwables_thrown_display},
    'vehicles': {'name': 'vehicles destroyed', 'value': rwr.constants.PlayersSort.VEHICLES_DESTROYED.value, 'getter': lambda player: player.vehicles_destroyed_display},
    'targets': {'name': 'targets destroyed', 'value': rwr.constants.PlayersSort.TARGETS_DESTROYED.value, 'getter': lambda player: player.targets_destroyed_display},
}

VALID_EVOLUTION_TYPES = {
    'ratio': {'name': 'K/D ratio', 'column': 'kd_ratio'},
    'score': {'name': 'score', 'column': 'score'},
    'position': {'name': 'position (by XP)', 'column': 'leaderboard_position'},
}

VALID_EVOLUTION_TYPE_NAMES = VALID_EVOLUTION_TYPES.keys()

VALID_SERVER_TYPES = {
    'vanilla': 'vanilla',
    'pacific': 'pacific',
    'rwd': 'Running_with_the_Dead'
}

EMBED_COLOR = 10800919 # The well-known primary RWRS color #A4CF17, in the decimal format
PLAYERS_LIMIT = 24
SERVERS_LIMIT = 10

AVAILABLE_COMMANDS = OrderedDict([
    ('stats', {'description': 'Displays stats about a given player', 'admin_only': False}),
    ('top', {'description': 'Displays the top 24 players', 'admin_only': False}),
    ('pos', {'description': 'Highlights the given player in the leaderboard', 'admin_only': False}),
    ('compare', {'description': 'Compare stats of two players', 'admin_only': False}),
    ('evolution', {'description': 'Displays the evolution of the specified stat', 'admin_only': False}),
    ('whereis', {'description': 'Displays information about the server the given player is playing on', 'admin_only': False}),
    ('server', {'description': 'Displays information about the given server', 'admin_only': False}),
    ('servers', {'description': 'Displays the first 10 currently active servers with room', 'admin_only': False}),
    ('now', {'description': 'Displays numbers about the current players and servers', 'admin_only': False}),
    ('info', {'description': 'Displays information about the bot', 'admin_only': False}),
    ('say', {'description': 'Makes the bot to say something', 'admin_only': True}),
    ('cc', {'description': 'Clears the RWRS cache', 'admin_only': True}),
    ('maintenance', {'description': 'Enables or disables the maintenance mode', 'admin_only': True}),
    ('motd', {'description': 'Sets or removes the MOTD', 'admin_only': True}),
    ('event', {'description': 'Sets or removes the next RWR event', 'admin_only': True})
])

AVAILABLE_COMMANDS_NAMES = AVAILABLE_COMMANDS.keys()
AVAILABLE_PUBLIC_COMMANDS_NAMES = [name for name, info in AVAILABLE_COMMANDS.items() if not info['admin_only']]
