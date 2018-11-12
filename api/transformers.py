from collections import OrderedDict
from flask_restful import fields


server_map_simple = OrderedDict([
    ('id', fields.String),
    ('name', fields.String(attribute='name_display')),
])

server_map_full = server_map_simple.copy()
server_map_full.update(OrderedDict([
    ('preview_image_url', fields.String(attribute='preview_absolute')),
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

server_simple = OrderedDict([
    ('name', fields.String),
    ('type_id', fields.String(attribute='type')),
    ('type_name', fields.String),
    ('mode_id', fields.String(attribute='mode')),
    ('mode_name', fields.String),
    ('database_id', fields.String(attribute='database')),
    ('database_name', fields.String),
    ('is_ranked', fields.Boolean),
    ('website_url', fields.String(attribute='website')),
    ('url', fields.String(attribute='link_absolute')),
    ('map', fields.Nested(server_map_simple)),
    ('players', fields.Nested(server_players_simple)),
    ('location', fields.Nested(server_location)),
])

server_full = server_simple.copy()
server_full.update(OrderedDict([
    ('version', fields.String),
    ('mode_name_long', fields.String),
    ('is_dedicated', fields.Boolean),
    ('comment', fields.String),
    ('bots', fields.Integer),
    ('map', fields.Nested(server_map_full)),
    ('players', fields.Nested(server_players_full)),
]))
