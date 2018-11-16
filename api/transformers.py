from collections import OrderedDict
from flask_restful import fields

database = OrderedDict([
    ('id', fields.String(attribute='database')),
    ('name', fields.String(attribute='database_name')),
])

player_simple = OrderedDict([
    ('username', fields.String),
    ('url', fields.String(attribute='link_absolute')),
    ('is_rwrs_creator', fields.Boolean(attribute='is_me')),
    ('is_contributor', fields.Boolean),
    ('is_rwr_dev', fields.Boolean),
    ('is_ranked_servers_admin', fields.Boolean),
])

server_map_simple = OrderedDict([
    ('id', fields.String),
    ('name', fields.String(attribute='name_display')),
])

server_map_full = server_map_simple.copy()
server_map_full.update(OrderedDict([
    ('preview_image_url', fields.String(attribute='preview_absolute')),
    ('minimap_image_url', fields.String(attribute='minimap_absolute')),
]))

server_location = OrderedDict([
    ('name', fields.String(attribute='text')),
    ('country_code', fields.String),
])

server_type = OrderedDict([
    ('id', fields.String(attribute='type')),
    ('name', fields.String(attribute='type_name')),
])

server_mode_simple = OrderedDict([
    ('id', fields.String(attribute='mode')),
    ('name', fields.String(attribute='mode_name')),
])

server_mode_full = server_mode_simple.copy()
server_mode_full.update(OrderedDict([
    ('name_long', fields.String(attribute='mode_name_long')),
]))

server_players_simple = OrderedDict([
    ('current', fields.Integer),
    ('max', fields.Integer),
    ('free', fields.Integer),
])

server_players_full = server_players_simple.copy()
server_players_full.update(OrderedDict([
    ('list', fields.List(fields.Nested(player_simple))), # Player usernames are replaced by objects in the API controller
]))

server_simple = OrderedDict([
    ('name', fields.String),
    ('ip', fields.String),
    ('port', fields.Integer),
    ('is_ranked', fields.Boolean),
    ('website_url', fields.String(attribute='website')),
    ('url', fields.String(attribute='link_absolute')),
    ('type', fields.Nested(server_type, attribute=lambda server: server)),
    ('mode', fields.Nested(server_mode_simple, attribute=lambda server: server)),
    ('database', fields.Nested(database, attribute=lambda server: server)),
    ('map', fields.Nested(server_map_simple)),
    ('players', fields.Nested(server_players_simple)),
    ('location', fields.Nested(server_location)),
])

server_full = server_simple.copy()
server_full.update(OrderedDict([
    ('version', fields.String),
    ('is_dedicated', fields.Boolean),
    ('comment', fields.String),
    ('bots', fields.Integer),
    ('mode', fields.Nested(server_mode_full, attribute=lambda server: server)),
    ('map', fields.Nested(server_map_full)),
    ('players', fields.Nested(server_players_full)),
]))

player_stats = OrderedDict([
    ('kills', fields.Integer),
    ('deaths', fields.Integer),
    ('score', fields.Integer),
    ('kd_ratio', fields.Float),
    ('time_played', fields.Integer),
    ('longest_kill_streak', fields.Integer),
    ('targets_destroyed', fields.Integer),
    ('vehicles_destroyed', fields.Integer),
    ('soldiers_healed', fields.Integer),
    ('teamkills', fields.Integer),
    ('distance_moved', fields.Float),
    ('shots_fired', fields.Integer),
    ('throwables_thrown', fields.Integer),
    ('xp', fields.Integer),
])

player_stats_list = player_stats.copy()
player_stats_list.update(OrderedDict([
    ('leaderboard_position', fields.Integer),
]))

player_rank = OrderedDict([
    ('id', fields.Integer),
    ('name', fields.String),
    ('alternative_name', fields.String),
    ('required_xp', fields.Integer(attribute='xp')),
    ('image_url', fields.String(attribute='image_absolute')),
    ('icon_url', fields.String(attribute='icon_absolute')),
])

# TODO Add date for player profile retrieved for a specific date / player stats history
player_full = player_simple.copy()
player_full.update(OrderedDict([
    ('database', fields.Nested(database, attribute=lambda player: player)),
    ('current_server', fields.Nested(server_simple, attribute='playing_on_server', allow_null=True)),
    ('stats', fields.Nested(player_stats, attribute=lambda player: player)),
    ('current_rank', fields.Nested(player_rank, attribute='rank')),
    ('next_rank', fields.Nested(player_rank)),
    ('xp_to_next_rank', fields.Integer),
    ('xp_percent_completion_to_next_rank', fields.Float),
]))
