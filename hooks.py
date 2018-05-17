from flask import g, abort, render_template, make_response
from werkzeug.exceptions import HTTPException
from models import RwrRootServer
from rwrs import app, auth
import rwr.scraper
import steam_api
import os


@app.before_request
def define_globals():
    g.INCLUDE_WEB_ANALYTICS = not app.config['DEBUG']
    g.UNDER_MAINTENANCE = False
    g.LAYOUT = 'normal'


@app.before_request
def set_beta_data():
    if app.config['BETA']:
        from git import Repo

        repo = Repo(app.root_path)

        g.BETA_BRANCH = repo.active_branch.name
        g.BETA_COMMIT = repo.head.commit.hexsha


@app.before_request
def check_under_maintenance():
    if os.path.exists('maintenance'):
        g.UNDER_MAINTENANCE = True

        abort(503)


@app.before_request
def get_counts():
    scraper = rwr.scraper.DataScraper()
    steam_api_client = steam_api.Client(app.config['STEAM_API_KEY'])

    g.all_players_with_servers_details = scraper.get_all_players_with_servers_details()

    online_players, active_servers, total_servers = scraper.get_counters()

    g.total_players = steam_api_client.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])
    g.online_players = online_players
    g.active_servers = active_servers
    g.total_servers = total_servers


@app.before_request
def get_rwr_root_server_global_status():
    g.is_online_multiplayer_ok = RwrRootServer.are_rwr_root_servers_ok()


@app.before_request
def get_motd():
    g.motd = None

    if os.path.exists('motd'):
        with open('motd', 'r', encoding='utf-8') as f:
            g.motd = f.read()


@app.before_request
def check_beta_access():
    if app.config['BETA']:
        @auth.login_required
        def _check_login():
            return None

        return _check_login()


@auth.get_password
def get_password(username):
    if username in app.config['BETA_USERS']:
        return app.config['BETA_USERS'].get(username)

    return None


@auth.error_handler
def auth_error():
    return http_error_handler(403, without_code=True)


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
