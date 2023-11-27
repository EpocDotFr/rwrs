from rwrs.models import Variable
from app import app, db, cache
import rwr.scraper
import arrow
import re

VARIABLE_NAME = 'event'

IP_PORT_REGEX = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}')


class ManualEventAlreadySetError(Exception):
    pass


def remove(force=False):
    if force or Variable.get_value(VARIABLE_NAME):
        Variable.set_value(VARIABLE_NAME, None)

        db.session.commit()

        cache.delete_memoized(rwr.scraper.get_servers)

        return True

    return False


def save(name, start_time, end_time=None, servers_address=None, manual=True):
    start_time = arrow.get(start_time).floor('minute')

    if end_time:
        end_time = arrow.get(end_time).floor('minute')

    if isinstance(servers_address, str):
        servers_address = servers_address.split(',')
    elif not servers_address:
        servers_address = []

    Variable.set_value(VARIABLE_NAME, {
        'name': name,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat() if end_time else None,
        'servers_address': servers_address,
        'manual': manual
    })

    db.session.commit()

    cache.delete_memoized(rwr.scraper.get_servers)


def save_from_discord():
    local_event = Variable.get_value(VARIABLE_NAME)

    if local_event and local_event['manual']:
        raise ManualEventAlreadySetError()

    # TODO Fetch event from Discord
    # TODO Sort events by starting date DESC
    # TODO Take the first one

    discord_event = {
        'name': 'Caca',
        'description': 'Will happen https://rwrstats.com/servers/162.248.88.126:1236/invasionus1 and 162.248.88.126:1236 [here](https://rwrstats.com/servers/47.107.163.15:1280/ww2invasioncn2) and 45.32.63.85:1280 mates',
        'scheduled_start_time': '2023-11-27T14:00:00+01:00',
        'scheduled_end_time': None,
        'status': 'SCHEDULED',
        'entity_metadata': {
            'location': '31.186.250.67:1260 31.186.250.67:1260',
        },
    }

    if discord_event:
        if discord_event['status'] in ('COMPLETED', 'CANCELED'):
            if local_event:
                remove(force=True)
        elif discord_event['status'] in ('SCHEDULED', 'ACTIVE'):
            name = discord_event['name']

            try:
                description = discord_event['description'] or ''
            except KeyError:
                description = ''

            try:
                location = discord_event['entity_metadata']['location'] or ''
            except KeyError:
                location = ''

            start_time = discord_event['scheduled_start_time']
            end_time = discord_event['scheduled_end_time'] or None

            servers_address = set()
            servers_address.update(IP_PORT_REGEX.findall(name))
            servers_address.update(IP_PORT_REGEX.findall(description))
            servers_address.update(IP_PORT_REGEX.findall(location))

            save(
                name,
                start_time,
                end_time=end_time,
                servers_address=sorted(servers_address),
                manual=False
            )
    elif local_event:
        remove(force=True)


def get(with_servers=True):
    event = Variable.get_value(VARIABLE_NAME)

    if not event:
        return None

    event_start_time = arrow.get(event['start_time'])
    event_end_time = arrow.get(event['end_time']) if event['end_time'] else None
    now_in_event_timezone = arrow.utcnow().to(event_start_time.tzinfo)

    if event_end_time and now_in_event_timezone >= event_end_time:
        return None

    event['start_time'] = event_start_time
    event['end_time'] = event_end_time
    event['is_ongoing'] = now_in_event_timezone >= event_start_time
    event['display_server_players_count'] = now_in_event_timezone >= event_start_time.shift(minutes=-15)
    event['servers'] = [
        rwr.scraper.get_server_by_ip_and_port(address) for address in event['servers_address']
    ] if with_servers else []

    return event
