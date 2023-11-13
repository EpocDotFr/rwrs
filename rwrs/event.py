from app import app, db, cache, discord_interactions
from rwrs.models import Variable
import rwr.scraper
import requests
import arrow

VARIABLE_NAME = 'event'


def remove():
    if Variable.get_value(VARIABLE_NAME):
        Variable.set_value(VARIABLE_NAME, None)

        db.session.commit()

        cache.delete_memoized(rwr.scraper.get_servers)

        return True

    return False


def set(name, start_time, end_time=None, servers_address=None, manual=True):
    arrow.get(start_time, app.config['EVENT_DATETIME_STORAGE_FORMAT'])  # Just to validate

    if end_time:
        arrow.get(end_time, app.config['EVENT_DATETIME_STORAGE_FORMAT'])  # Just to validate

    Variable.set_value(VARIABLE_NAME, {
        'name': name,
        'start_time': start_time,
        'end_time': end_time,
        'servers_address': servers_address.split(',') if servers_address else [],
        'manual': manual
    })

    db.session.commit()

    cache.delete_memoized(rwr.scraper.get_servers)


def set_from_discord():
    event = Variable.get_value(VARIABLE_NAME)

    if event and event['manual']:
        raise Exception('Aborting: an event has already been manually set')

    url = '{}/guilds/{}/scheduled-events'.format(
        app.config['DISCORD_BASE_URL'],
        app.config['DISCORD_GUILD'],
    )

    response = requests.get(url, headers=discord_interactions.auth_headers(app))

    response.raise_for_status()

    print(response.json())

    # TODO Pull from Discord and get most significant event from list
    # TODO Parse all IPs from event's location and description fields

    # TODO Save event
    # YYYY-MM-DD HH:mm ZZZ
    # set(name, start_time, end_time=None, servers_address=None, manual=False)


def get(with_servers=True):
    event = Variable.get_value(VARIABLE_NAME)

    if not event:
        return None

    event_start_time = arrow.get(event['start_time'], app.config['EVENT_DATETIME_STORAGE_FORMAT']).floor('minute')
    event_end_time = arrow.get(event['end_time'], app.config['EVENT_DATETIME_STORAGE_FORMAT']).floor('minute') if event['end_time'] else None
    now_in_event_timezone = arrow.now(event_start_time.tzinfo).floor('minute')

    if event_end_time and now_in_event_timezone >= event_end_time:
        return None

    event['start_time'] = event_start_time
    event['is_ongoing'] = now_in_event_timezone >= event_start_time
    event['display_server_players_count'] = now_in_event_timezone >= event_start_time.shift(minutes=-15)
    event['servers'] = [
        rwr.scraper.get_server_by_ip_and_port(address) for address in event['servers_address']
    ] if with_servers else []

    return event
