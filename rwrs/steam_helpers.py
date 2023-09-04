from steam.webapi import WebAPI as SteamAPIClient
from app import app, cache
import re

steam_api_client = SteamAPIClient(app.config['STEAM_API_KEY'])
_steam_identity_url_regex = re.compile('steamcommunity.com/openid/id/([0-9]+)$')


def parse_steam_id_from_identity_url(identity_url):
    """Extract the Steam ID from a Steam identity URL."""
    match = _steam_identity_url_regex.search(identity_url)

    if match:
        return match.group(1)

    return None


@cache.memoize(timeout=app.config['STEAM_PLAYERS_CACHE_TIMEOUT'])
def get_current_players_count_for_app(appid):
    response = steam_api_client.ISteamUserStats.GetNumberOfCurrentPlayers(appid=appid)

    if 'response' not in response or 'player_count' not in response['response']:
        return None

    return response['response']['player_count']


def get_user_summaries(steam_id):
    response = steam_api_client.ISteamUser.GetPlayerSummaries_v2(steamids=steam_id)

    if 'response' not in response or 'players' not in response['response'] or len(response['response']['players']) == 0:
        return None

    return response['response']['players'][0]
