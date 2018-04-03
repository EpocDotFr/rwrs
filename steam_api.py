from rwrs import app, cache
import requests

steam_api_requests_session = requests.Session()


class Client:
    endpoint_pattern = 'https://api.steampowered.com/{interface}/{method}/v{method_version}/'

    def __init__(self, api_key, output_format='json'):
        self.api_key = api_key
        self.output_format = output_format

    def _call(self, steam_interface, steam_method, steam_method_version=1, http_method='GET', params=None):
        """Perform an HTTP request to the Steam API endpoint."""
        url = self.endpoint_pattern.format(
            interface=steam_interface,
            method=steam_method,
            method_version=steam_method_version
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

        response = steam_api_requests_session.request(http_method, url, params=params_to_send, headers=headers)

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

        data = self._call('ISteamUserStats', 'GetNumberOfCurrentPlayers', params=params)

        return data['player_count']
