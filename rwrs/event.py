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


def set(name, datetime, servers_address, manual=True):
    arrow.get(datetime, app.config['EVENT_DATETIME_STORAGE_FORMAT'])  # Just to validate

    Variable.set_value(VARIABLE_NAME, {
        'name': name,
        'datetime': datetime,
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
    # datetime=YYYY-MM-DD HH:mm ZZZ
    # set(name, datetime, servers_address, manual=False)


def get(with_servers=True):
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
    event['servers'] = [
        rwr.scraper.get_server_by_ip_and_port(address) for address in event['servers_address']
    ] if with_servers else []

    return event
