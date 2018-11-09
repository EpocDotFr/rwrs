from collections import OrderedDict
from flask_restful import fields


server_map_fields = OrderedDict([
    ('name', fields.String(attribute='name_display')),
    ('preview_image_url', fields.String(attribute='preview_absolute')),
])

server_location_fields = OrderedDict([
    ('name', fields.String(attribute='text')),
    ('country_code', fields.String),
])

server_players_fields = OrderedDict([
    ('current', fields.Integer),
    ('max', fields.Integer),
    ('free', fields.Integer),
    ('list', fields.List(fields.String)),
])


server_fields = OrderedDict([
    ('name', fields.String),
    ('version', fields.String),
    ('type_name', fields.String),
    ('database_name', fields.String),
    ('mode_name', fields.String),
    ('mode_name_long', fields.String),
    ('is_ranked', fields.Boolean),
    ('is_dedicated', fields.Boolean),
    ('comment', fields.String),
    ('website_url', fields.String(attribute='website')),
    ('url', fields.String(attribute='link_absolute')),
    ('bots', fields.Integer),
    ('map', fields.Nested(server_map_fields)),
    ('players', fields.Nested(server_players_fields)),
    ('location', fields.Nested(server_location_fields)),
])
