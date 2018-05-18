from rwrs import app, cache
import requests
import arrow


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

        response = requests.get(url, params=params_to_send, headers=headers)

        response.raise_for_status()

        if self.output_format == 'json':
            data = response.json()

            if data['response']['result'] != 1:
                raise Exception('Response was not successful')

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


def get_game_events(game_id): # TODO Cache
    """Get the list of upcoming events for the specified Steam game."""
    return [ # TODO Implement
        {
            'name': 'Event name 1',
            'start': arrow.utcnow().floor('minute').shift(hours=+1),
            'url': 'https://steamcommunity.com/games/XXXX/events/XXXX'
        },
        {
            'name': 'Event name 2',
            'start': arrow.utcnow().floor('minute').shift(days=+1),
            'url': 'https://steamcommunity.com/games/XXXX/events/XXXX'
        },
        {
            'name': 'Event name 3',
            'start': arrow.utcnow().floor('minute').shift(days=+2),
            'url': 'https://steamcommunity.com/games/XXXX/events/XXXX'
        }
    ]
