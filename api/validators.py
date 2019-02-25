from flask_restful import reqparse, inputs
from rwrs import app
import rwr.constants
import iso3166
import arrow
import re

_location_regex = re.compile(r'^(?:any|(?P<location_code_single>[a-zA-Z]{2})|(?P<location_type>country|continent):(?P<location_code_with_type>[a-zA-Z]{2}))$')


def location(value):
    location_match = _location_regex.match(value)

    if not location_match:
        raise ValueError('Invalid format')

    location_match = location_match.groupdict()

    if location_match['location_code_single'] and location_match['location_code_single'].upper() not in iso3166.countries_by_alpha2:
        raise ValueError('Invalid country code')
    if location_match['location_type'] == 'continent' and location_match['location_code_with_type'].lower() not in rwr.constants.VALID_CONTINENTS:
        raise ValueError('Invalid continent code')
    elif location_match['location_type'] == 'country' and location_match['location_code_with_type'].upper() not in iso3166.countries_by_alpha2:
        raise ValueError('Invalid country code')

    return value


def arrow_date(value):
    try:
        value = arrow.get(value, 'YYYY-MM-DD')
    except Exception:
        raise ValueError('Invalid format')

    return value

maps_choices = ['any']
maps_choices.extend(rwr.constants.VALID_MAPS)

types_choices = ['any']
types_choices.extend(rwr.constants.VALID_SERVER_TYPES)

modes_choices = ['any']
modes_choices.extend(rwr.constants.VALID_SERVER_MODES)

limit_parser = reqparse.RequestParser()
limit_parser.add_argument('limit', location='args', type=inputs.int_range(1, app.config['LIST_PAGE_SIZES'][-1]), default=app.config['LIST_PAGE_SIZES'][0])

get_servers_list = reqparse.RequestParser()
get_servers_list.add_argument('location', location='args', type=location, default='any')
get_servers_list.add_argument('map', location='args', choices=maps_choices, default='any')
get_servers_list.add_argument('type', location='args', choices=types_choices, default='any')
get_servers_list.add_argument('mode', location='args', choices=modes_choices, default='any')
get_servers_list.add_argument('dedicated', location='args', type=inputs.boolean)
get_servers_list.add_argument('ranked', location='args', type=inputs.boolean)
get_servers_list.add_argument('not_empty', location='args', type=inputs.boolean)
get_servers_list.add_argument('not_full', location='args', type=inputs.boolean)
get_servers_list.add_argument('limit', location='args', type=inputs.positive)

get_players_list = limit_parser.copy()
get_players_list.add_argument('sort', location='args', choices=rwr.constants.VALID_PLAYERS_SORTS, default=rwr.constants.PlayersSort.SCORE.value)
get_players_list.add_argument('target', location='args', default=None)
get_players_list.add_argument('start', location='args', type=inputs.natural, default=0)

get_one_player = reqparse.RequestParser()
get_one_player.add_argument('date', location='args', type=arrow_date)

get_player_stats_history = limit_parser.copy()
get_player_stats_history.add_argument('page', location='args', type=inputs.positive, default=1)
