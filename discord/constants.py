from collections import OrderedDict
import rwr.constants
import helpers

VALID_PLAYER_SORTS = {
    'score': {'name': 'score', 'value': rwr.constants.PlayersSort.SCORE, 'getter': lambda player: player.score_display},
    'xp': {'name': 'experience', 'value': rwr.constants.PlayersSort.XP, 'getter': lambda player: player.xp_display},
    'kills': {'name': 'kills', 'value': rwr.constants.PlayersSort.KILLS, 'getter': lambda player: player.kills_display},
    'deaths': {'name': 'deaths', 'value': rwr.constants.PlayersSort.DEATHS, 'getter': lambda player: player.deaths_display},
    'ratio': {'name': 'K/D ratio', 'value': rwr.constants.PlayersSort.KD_RATIO, 'getter': lambda player: player.kd_ratio},
    'time': {'name': 'time played', 'value': rwr.constants.PlayersSort.TIME_PLAYED, 'getter': lambda player: helpers.humanize_seconds_to_hours(player.time_played)},
    'streak': {'name': 'longest kill streak', 'value': rwr.constants.PlayersSort.LONGEST_KILL_STREAK, 'getter': lambda player: player.longest_kill_streak_display},
    'tk': {'name': 'teamkills', 'value': rwr.constants.PlayersSort.TEAMKILLS, 'getter': lambda player: player.teamkills_display},
    'heals': {'name': 'soldiers healed', 'value': rwr.constants.PlayersSort.SOLDIERS_HEALED, 'getter': lambda player: player.soldiers_healed_display},
    'shots': {'name': 'shots fired', 'value': rwr.constants.PlayersSort.SHOTS_FIRED, 'getter': lambda player: player.shots_fired_display},
    'distance': {'name': 'distance moved (km)', 'value': rwr.constants.PlayersSort.DISTANCE_MOVED, 'getter': lambda player: player.distance_moved},
    'throws': {'name': 'throwables thrown', 'value': rwr.constants.PlayersSort.THROWABLES_THROWN, 'getter': lambda player: player.throwables_thrown_display},
    'vehicles': {'name': 'vehicles destroyed', 'value': rwr.constants.PlayersSort.VEHICLES_DESTROYED, 'getter': lambda player: player.vehicles_destroyed_display},
    'targets': {'name': 'targets destroyed', 'value': rwr.constants.PlayersSort.TARGETS_DESTROYED, 'getter': lambda player: player.targets_destroyed_display},
}

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
    ('whereis', {'description': 'Displays information about the server the given player is playing on', 'admin_only': False}),
    ('server', {'description': 'Displays information about the given server', 'admin_only': False}),
    ('servers', {'description': 'Displays the first 10 currently active servers with room', 'admin_only': False}),
    ('now', {'description': 'Displays numbers about the current players and servers', 'admin_only': False}),
    ('status', {'description': 'Displays the current status of the online multiplayer', 'admin_only': False}),
    ('events', {'description': 'Displays upcoming RWR events', 'admin_only': False}),
    ('info', {'description': 'Displays information about the bot', 'admin_only': False}),
    ('say', {'description': 'Makes the bot to say something', 'admin_only': True}),
    ('cc', {'description': 'Clears the RWRS cache', 'admin_only': True}),
    ('maintenance', {'description': 'Enables or disables the maintenance mode', 'admin_only': True}),
    ('motd', {'description': 'Sets or removes the MOTD', 'admin_only': True})
])

AVAILABLE_COMMANDS_NAMES = AVAILABLE_COMMANDS.keys()
AVAILABLE_PUBLIC_COMMANDS_NAMES = [name for name, info in AVAILABLE_COMMANDS.items() if not info['admin_only']]
