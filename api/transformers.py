from collections import OrderedDict
from flask_restful import fields


class ArrowDateField(fields.Raw):
    def format(self, value):
        return value.format('YYYY-MM-DD') if value else None

live_counters = OrderedDict([
    ('players', fields.Nested(OrderedDict([
        ('total', fields.Integer),
        ('online', fields.Integer),
    ]))),
    ('servers', fields.Nested(OrderedDict([
        ('total', fields.Integer),
        ('active', fields.Integer),
    ]))),
])

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
    ('database', fields.Nested(database, attribute=lambda player: player if player.database else None, allow_null=True)),
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
    ('flag_image_url', fields.String(attribute='flag_absolute')),
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
    ('mode', fields.Nested(server_mode_simple, attribute=lambda server: server if server.mode else None, allow_null=True)),
    ('database', fields.Nested(database, attribute=lambda server: server if server.database else None, allow_null=True)),
    ('map', fields.Nested(server_map_simple)),
    ('players', fields.Nested(server_players_simple)),
    ('location', fields.Nested(server_location, attribute=lambda server: server.location if server.location.country_code else None, allow_null=True)),
    ('steam_join_url', fields.String(attribute='steam_join_link')),
])

server_full = server_simple.copy()
server_full.update(OrderedDict([
    ('version', fields.String),
    ('is_dedicated', fields.Boolean),
    ('comment', fields.String),
    ('bots', fields.Integer),
    ('mode', fields.Nested(server_mode_full, attribute=lambda server: server if server.mode else None, allow_null=True)),
    ('map', fields.Nested(server_map_full)),
    ('players', fields.Nested(server_players_full)),
    ('banner_image_url', fields.String(attribute='banner_absolute'))
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
    ('position', fields.Integer(attribute='leaderboard_position')),
]))

player_rank = OrderedDict([
    ('id', fields.Integer),
    ('name', fields.String),
    ('alternative_name', fields.String),
    ('required_xp', fields.Integer(attribute='xp')),
    ('image_url', fields.String(attribute='image_absolute')),
    ('icon_url', fields.String(attribute='icon_absolute')),
])

player_stats_history = player_stats_list.copy()
player_stats_history.update(OrderedDict([
    ('date', ArrowDateField(attribute='created_at')),
    ('promoted_to_rank', fields.Nested(player_rank, allow_null=True)),
]))

player_list = player_simple.copy()
player_list.update(OrderedDict([
    ('position', fields.Integer(attribute='leaderboard_position')),
    ('current_server', fields.Nested(server_simple, attribute='playing_on_server', allow_null=True)),
    ('stats', fields.Nested(player_stats, attribute=lambda player: player)),
    ('current_rank', fields.Nested(player_rank, attribute='rank')),
]))

player_full = player_list.copy()

del player_full['position']

player_full.update(OrderedDict([
    ('next_rank', fields.Nested(player_rank, allow_null=True)),
    ('xp_to_next_rank', fields.Integer),
    ('xp_percent_completion_to_next_rank', fields.Float),
    ('date', ArrowDateField(attribute='created_at')), # Added in the API controller
    ('signature_image_url', fields.String(attribute='signature_absolute')),
    ('promoted_to_rank', fields.Nested(player_rank, allow_null=True)), # Added in the API controller
]))
