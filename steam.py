from lxml import html, etree
from rwrs import app, cache
import requests
import arrow

steam_requests_session = requests.Session()


class SteamworksApiClient:
    steamworks_api_endpoint = 'https://api.steampowered.com/{interface}/{method}/v{method_version}/'

    def __init__(self, api_key, output_format='json'):
        self.api_key = api_key
        self.output_format = output_format

    def _call_steamworks_api(self, interface, method, method_version=1, params=None):
        """Perform an HTTP request to the Steamworks API endpoint."""
        url = self.steamworks_api_endpoint.format(
            interface=interface,
            method=method,
            method_version=method_version
        )

        headers = {
            'User-Agent': 'rwrstats.com'
        }

        params_to_send = {
            'key': self.api_key,
            'format': self.output_format
        }

        if params:
            params_to_send.update(params)

        response = steam_requests_session.get(url, params=params_to_send, headers=headers)

        response.raise_for_status()

        if self.output_format == 'json':
            data = response.json()

            if 'result' in data['response']:
                if data['response']['result'] != 1:
                    raise Exception('Steamworks response was not successful')

                del data['response']['result']

            return data['response']
        else:
            raise NotImplemented('Output format {} not supported'.format(self.output_format))

    @cache.memoize(timeout=app.config['STEAM_PLAYERS_CACHE_TIMEOUT'])
    def get_current_players_count_for_app(self, appid):
        """Get the number of current players for a specific application."""
        params = {
            'appid': appid
        }

        data = self._call_steamworks_api('ISteamUserStats', 'GetNumberOfCurrentPlayers', params=params)

        return data['player_count']

    def get_user_summaries(self, steam_id):
        """Return information about a specific user."""
        params = {
            'steamids': steam_id
        }

        data = self._call_steamworks_api('ISteamUser', 'GetPlayerSummaries', method_version=2, params=params)

        return data['players'][0] if 'players' in data and len(data['players']) == 1 else None


def get_group_events(group_or_game_id, is_official=False, year=None, month=None):
    """Get the list of upcoming events for the specified Steam game."""
    url = 'https://steamcommunity.com/{what}/{group_or_game_id}/events'.format(
        what='games' if is_official else 'gid',
        group_or_game_id=group_or_game_id
    )

    headers = {
        'User-Agent': 'rwrstats.com'
    }

    now = arrow.utcnow()

    year = year if year is not None else now.format('YYYY')
    month = month if month is not None else now.format('M')

    params = {
        'xml': 1,
        'action': 'eventFeed',
        'year': year,
        'month': month,
        '_': now.timestamp
    }

    response = requests.get(url, params=params, headers=headers)

    response.raise_for_status()

    response_tree = etree.fromstring(response.content)

    if response_tree.findtext('results') != 'OK':
        raise Exception('Response is erronous')

    ret = []

    for event in response_tree.xpath('(/response/expiredEvent | /response/event)/text()'):
        event_tree = html.fromstring(event)

        event_start_day = event_tree.findtext('./div[@class="eventDateBlock"]/span[1]').split(' ', maxsplit=1)[1]
        event_start_time = event_tree.findtext('./div[@class="eventDateBlock"]/span[2]')

        # FIXME
        event_start = arrow.get('{} {} {} {}'.format(year, month, event_start_day, event_start_time), 'YYYY M D hh:mma')

        if event_start.floor('day') < now.floor('day'):
            continue

        event_name = event_tree.findtext('./div[@class="eventBlockTitle"]/a[@class="headlineLink"]')
        event_url = event_tree.find('./div[@class="eventBlockTitle"]/a[@class="headlineLink"]').get('href')

        ret.append({
            'name': event_name,
            'start': event_start,
            'url': event_url
        })

    return ret
