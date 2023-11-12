from rwrs.models import Variable
from app import app
import rwr.scraper
import arrow

VARIABLE_NAME = 'event'


def remove():
    if Variable.get_value(VARIABLE_NAME):
        Variable.set_value(VARIABLE_NAME, None)

        return True

    return False


def set(name, datetime, server_ip_and_port):
    arrow.get(datetime, app.config['EVENT_DATETIME_STORAGE_FORMAT'])  # Just to validate

    Variable.set_value(VARIABLE_NAME, {
        'name': name,
        'datetime': datetime,
        'server_ip_and_port': server_ip_and_port
    })


def get(with_server=True):
    event = Variable.get_value(VARIABLE_NAME)

    if not event:
        return None

    event_datetime = arrow.get(event['datetime'], app.config['EVENT_DATETIME_STORAGE_FORMAT']).floor('minute')
    now_in_event_timezone = arrow.now(event_datetime.tzinfo).floor('minute')

    if now_in_event_timezone >= event_datetime.shift(hours=+5):
        return None

    event['datetime'] = event_datetime
    event['is_ongoing'] = now_in_event_timezone >= event_datetime
    event['display_server_players_count'] = now_in_event_timezone >= event_datetime.shift(minutes=-15)
    event['server'] = rwr.scraper.get_server_by_ip_and_port(event['server_ip_and_port']) if with_server and event[
        'server_ip_and_port'] else None

    return event
