from collections import OrderedDict
from flask_restful import fields


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

server_players_simple = OrderedDict([
    ('current', fields.Integer),
    ('max', fields.Integer),
    ('free', fields.Integer),
])

server_players_full = server_players_simple.copy()
server_players_full.update(OrderedDict([
    ('list', fields.List(fields.String)),
]))

server_type = OrderedDict([
    ('id', fields.String(attribute='type')),
    ('name', fields.String(attribute='type_name')),
])

server_database = OrderedDict([
    ('id', fields.String(attribute='database')),
    ('name', fields.String(attribute='database_name')),
])

server_mode_simple = OrderedDict([
    ('id', fields.String(attribute='mode')),
    ('name', fields.String(attribute='mode_name')),
])

server_mode_full = server_mode_simple.copy()
server_mode_full.update(OrderedDict([
    ('name_long', fields.String(attribute='mode_name_long')),
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
    ('database', fields.Nested(server_database, attribute=lambda server: server)),
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
