from flask import g, abort, render_template, make_response, request, redirect, flash, url_for
from rwrs import app, login_manager, oid, db
from werkzeug.exceptions import HTTPException
from models import User, Variable
from flask_login import login_user
from datetime import datetime
import steam_helpers
import rwr.scraper
import bugsnag
import arrow
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@oid.after_login
def create_or_login(resp):
    steam_id = steam_helpers.parse_steam_id_from_identity_url(resp.identity_url)

    try:
        steam_user_info = steam_helpers.get_user_summaries(steam_id)

        if not steam_user_info:
            raise Exception('Unable to get Steam user info for Steam ID {}'.format(steam_id))
    except Exception as e:
        bugsnag.notify(e)

        flash('An error occured while fetching your Steam account information. Please try again.', 'error')

        return redirect(url_for('sign_in'))

    user, user_was_created = User.get_by_steam_id(steam_id, create_if_unexisting=True)

    user.username = steam_user_info['personaname']
    user.small_avatar_url = steam_user_info['avatar']
    user.large_avatar_url = steam_user_info['avatarfull']
    user.country_code = steam_user_info['loccountrycode'].lower() if 'loccountrycode' in steam_user_info and steam_user_info['loccountrycode'] else None
    user.last_login_at = arrow.utcnow().floor('minute')

    if user_was_created:
        user.is_profile_public = True if 'communityvisibilitystate' in steam_user_info and steam_user_info['communityvisibilitystate'] == 3 else False

    db.session.add(user)

    try:
        user.sync_rwr_accounts()
    except Exception as e:
        raise e
        bugsnag.notify(e)

        flash('An error occured while syncing your RWR accounts. Please try again.', 'error')

        return redirect(url_for('sign_in'))

    db.session.commit()

    login_user(user, remember=True)

    flash('Welcome, {}!'.format(user.username), 'success')

    return redirect(url_for('home'))


@app.before_request
def before_request():
    if request.endpoint == 'static':
        return

    g.UNDER_MAINTENANCE = os.path.exists('maintenance')

    if request.endpoint in ('dynamic_player_image', 'dynamic_server_image'):
        return

    g.MOTD = Variable.get_value('motd')
    g.EVENT = Variable.get_event()

    if request.path == app.config['DISCORD_INTERACTIONS_PATH']:
        return

    g.INCLUDE_WEB_ANALYTICS = not app.config['DEBUG']
    g.LAYOUT = 'normal'

    if g.UNDER_MAINTENANCE:
        abort(503)

        return

    online_players, active_servers, total_servers = rwr.scraper.get_counters()

    g.total_players = steam_helpers.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])
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
