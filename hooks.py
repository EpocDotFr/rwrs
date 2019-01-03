from flask import g, abort, render_template, make_response, request
from werkzeug.exceptions import HTTPException
from datetime import datetime
from rwrs import app
import rwr.scraper
import steam
import os


@app.before_request
def define_globals():
    g.UNDER_MAINTENANCE = False

    if request.endpoint in ('dynamic_player_image', 'dynamic_server_image'):
        return

    g.INCLUDE_WEB_ANALYTICS = not app.config['DEBUG']
    g.LAYOUT = 'normal'


@app.before_request
def set_beta_data():
    if request.endpoint in ('dynamic_player_image', 'dynamic_server_image') or not app.config['BETA']:
        return

    from git import Repo

    repo = Repo(app.root_path)

    g.BETA_BRANCH = repo.active_branch.name
    g.BETA_COMMIT = repo.head.commit.hexsha


@app.before_request
def get_motd():
    if request.endpoint in ('dynamic_player_image', 'dynamic_server_image'):
        return

    g.MOTD = None

    if os.path.exists('motd'):
        with open('motd', 'r', encoding='utf-8') as f:
            g.MOTD = f.read()


@app.before_request
def check_under_maintenance():
    g.UNDER_MAINTENANCE = os.path.exists('maintenance')

    if request.endpoint in ('dynamic_player_image', 'dynamic_server_image') or not g.UNDER_MAINTENANCE:
        return

    abort(503)


@app.before_request
def get_counts():
    if request.endpoint in ('dynamic_player_image', 'dynamic_server_image'):
        return

    steamworks_api_client = steam.SteamworksApiClient(app.config['STEAM_API_KEY'])

    g.all_players_with_servers_details = rwr.scraper.get_all_players_with_servers_details()

    online_players, active_servers, total_servers = rwr.scraper.get_counters()

    g.total_players = steamworks_api_client.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])
    g.online_players = online_players
    g.active_servers = active_servers
    g.total_servers = total_servers


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}


@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(503)
def http_error_handler(error, without_code=False):
    if isinstance(error, HTTPException):
        error = error.code
    elif not isinstance(error, int):
        error = 500

    body = render_template('errors/{}.html'.format(error))

    if not without_code:
        return make_response(body, error)
    else:
        return make_response(body)
