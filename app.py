from flask import Flask, redirect, flash, url_for, request, g, abort, render_template
from flask_login import LoginManager, current_user, login_user
from flask_discord_interactions import DiscordInteractions
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, AdminIndexView
from werkzeug.exceptions import HTTPException
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_openid import OpenID
from flask_caching import Cache
from datetime import datetime
from environs import Env
import arrow
import math
import os

# -----------------------------------------------------------
# App bootstrap

env = Env()
env.read_env()

app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py') # TODO

# -----------------------------------------------------------
# Debugging-related behaviours

if app.config['DEBUG']:
    import logging

    logging.basicConfig(level=logging.DEBUG)
elif app.config['SENTRY_DSN']:
    try:
        from sentry_sdk.integrations.flask import FlaskIntegration
        import sentry_sdk

        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[
                FlaskIntegration(),
            ],
            traces_sample_rate=app.config['SENTRY_TRACES_SAMPLE_RATE']
        )
    except ImportError:
        pass

import helpers

app.config['SQLALCHEMY_DATABASE_URI'] = helpers.build_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'FileSystemCache'
app.config['CACHE_DIR'] = 'instance/cache'
app.config['CACHE_THRESHOLD'] = 10000
app.config['RANKS_IMAGES_DIR'] = 'static/images/ranks'
app.config['RANKS_DATA_FILE'] = 'data/ranks.json'
app.config['MINIMAPS_IMAGES_DIR'] = 'static/images/maps/minimap'
app.config['MAPS_PREVIEW_IMAGES_DIR'] = 'static/images/maps/preview'
app.config['MAPS_DATA_FILE'] = 'data/maps.json'
app.config['GEOIP_DATABASE_FILE'] = 'instance/GeoLite2-City.mmdb'
app.config['OFFICIAL_SERVERS_MODS_FILE'] = 'data/official_servers_mods.json'
app.config['MY_USERNAME'] = 'epocdotfr'
app.config['CONTRIBUTORS'] = ['street veteran', 'mastock', 'dio', 'jatimatik', 'mellcor', 'teratai', 'harrified', 'mr. bang', 'dogtato', 'stesmith', 'korgorr', 'foxtrod', 'moorsey100', 'moorsey the owl', 'kilroy (7kb/s)']
app.config['DEVS'] = ['jackmayol', 'pasik', 'pasik2', 'tremozl', 'the soldier', '577', 'unit g17']
app.config['LIST_PAGE_SIZES'] = [15, 30, 50, 100]
app.config['RWR_STEAM_APP_ID'] = 270150
app.config['EVENT_DATETIME_STORAGE_FORMAT'] = 'YYYY-MM-DD HH:mm ZZZ'
app.config['EVENT_DATETIME_DISPLAY_FORMAT'] = 'MMMM Do, YYYY @ h:mm A ZZZ'
app.config['STATUS_PAGE_URL'] = 'https://stats.uptimerobot.com/Z0PkQf9YY'
app.config['DISCORD_SERVER_URL'] = 'https://discord.gg/runningwithrifles'
app.config['BUNDLE_ERRORS'] = True
app.config['SESSION_PROTECTION'] = 'basic'
app.config['DISCORD_INTERACTIONS_PATH'] = '/discord-interactions'
app.config['MY_DISCORD_ID'] = '66543750725246976'
app.config['OFFICIAL_SERVERS_MODS'] = helpers.load_json(app.config['OFFICIAL_SERVERS_MODS_FILE'])
app.config['ASSETS_CACHE'] = 'instance/webassets-cache'

# -----------------------------------------------------------
# Flask extensions initialization and configuration

# Flask-DebugToolbar
if app.config['DEBUG']:
    try:
        from flask_debugtoolbar import DebugToolbarExtension

        debug_toolbar = DebugToolbarExtension(app)
    except ImportError:
        pass

# Flask-Compress
try:
    from flask_compress import Compress

    compress = Compress(app)
except ImportError:
    pass

# Flask-HTMLmin
try:
    from flask_htmlmin import HTMLMIN

    htmlmin = HTMLMIN(app)
except ImportError:
    pass

# Flask-Assets
assets = Environment(app)
assets.append_path('assets')

assets.register('js_popovers', Bundle('js/popovers.js', filters='jsmin', output='js/popovers.min.js'))
assets.register('js_popovers_rwr_accounts_sync', Bundle('js/popovers.js', 'js/rwr_accounts_sync.js', filters='jsmin', output='js/popovers_rwr_accounts_sync.min.js'))
assets.register('js_charts', Bundle('js/charts.js', filters='jsmin', output='js/charts.min.js'))
assets.register('js_charts_popovers', Bundle('js/charts.js', 'js/popovers.js', filters='jsmin', output='js/charts_popovers.min.js'))
assets.register('js_regenerate_pat', Bundle('js/regenerate_pat.js', filters='jsmin', output='js/regenerate_pat.min.js'))
assets.register('js_rwr_account_deletion', Bundle('js/rwr_account_deletion.js', filters='jsmin', output='js/rwr_account_deletion.min.js'))
assets.register('css_app', Bundle('css/flags.css', 'css/app.css', filters='cssutils', output='css/app.min.css'))

# Flask-SQLAlchemy
db = SQLAlchemy(app)

# Flask-Migrate
migrate = Migrate(app, db)

# Flask-Caching
cache = Cache(app)

# Flask-Login
login_manager = LoginManager(app)
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    from models import User

    return User.query.get(user_id)

# Flask-OpenID
oid = OpenID(app)


@oid.after_login
def create_or_login(resp):
    from steam_helpers import parse_steam_id_from_identity_url, get_user_summaries
    from models import User

    steam_id = parse_steam_id_from_identity_url(resp.identity_url)

    try:
        steam_user_info = get_user_summaries(steam_id)

        if not steam_user_info:
            raise Exception('Unable to get Steam user info for Steam ID {}'.format(steam_id))
    except Exception:
        app.logger.exception(f'Error fetching Steam account information #{steam_id}')

        if not app.config['DEBUG'] and app.config['SENTRY_DSN']:
            import sentry_sdk

            sentry_sdk.capture_exception()

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

        db.session.commit()
    except Exception:
        app.logger.exception(f'Error syncing RWR accounts for user #{user.id} on login')

        if not app.config['DEBUG'] and app.config['SENTRY_DSN']:
            import sentry_sdk

            sentry_sdk.capture_exception()

        flash('An error occured while syncing your RWR accounts. Please try again.', 'error')

        return redirect(url_for('sign_in'))

    login_user(user, remember=True)

    flash('Welcome, {}!'.format(user.username), 'success')

    return redirect(url_for('home'))

# Flask-Discord-Interactions
discord_interactions = DiscordInteractions(app)
discord_interactions.set_route(app.config['DISCORD_INTERACTIONS_PATH'])

# Flask-Admin
class RestrictedView:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_rwrs_admin

    def inaccessible_callback(self, name, **kwargs):
        abort(404)


class RestrictedAdminIndexView(RestrictedView, AdminIndexView):
    pass

class RestrictedModelView(RestrictedView, ModelView):
    pass

admin = Admin(app, name='RWRS Admin', template_mode='bootstrap4', url='/manage', index_view=RestrictedAdminIndexView(url='/manage'))

# -----------------------------------------------------------
# Pre-request hooks

@app.before_request
def before_request():
    from steam_helpers import get_current_players_count_for_app
    from models import Variable
    import rwr.scraper

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

    online_players, active_servers, total_servers = rwr.scraper.get_counters()

    g.total_players = get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])
    g.online_players = online_players
    g.active_servers = active_servers
    g.total_servers = total_servers

# -----------------------------------------------------------
# Context processors

@app.context_processor
def context_processor():
    return {
        'current_year': datetime.now().year,
    }

# -----------------------------------------------------------
# Jinja alterations

import rwr.constants
import rwr.utils

app.jinja_env.filters.update(
    humanize_seconds_to_days=helpers.humanize_seconds_to_days,
    humanize_seconds_to_hours=helpers.humanize_seconds_to_hours,
    humanize_integer=helpers.humanize_integer,
    simplified_integer=helpers.simplified_integer,
    markdown_to_html_inline=helpers.markdown_to_html_inline
)

app.jinja_env.globals.update(
    int=int,
    float=float,
    str=str,
    round=round,
    abs=abs,
    fabs=math.fabs,
    isinstance=isinstance,
    PlayersSort=rwr.constants.PlayersSort,
    merge_query_string_params=helpers.merge_query_string_params,
    get_database_name=rwr.utils.get_database_name,
    PLAYERS_LIST_DATABASES=rwr.constants.PLAYERS_LIST_DATABASES,
    generate_next_url=helpers.generate_next_url
)

# -----------------------------------------------------------
# Error pages

@app.errorhandler(HTTPException)
def http_error_handler(e):
    return render_template(f'errors/{e.code}.html'), e.code

# -----------------------------------------------------------
# After-bootstrap imports

import models
import routes
import commands
import discord.commands
import api

# Flask-Admin

admin.add_view(RestrictedModelView(models.RwrAccount, db.session, name='RWR Accounts', url='rwr-accounts'))
admin.add_view(RestrictedModelView(models.RwrAccountStat, db.session, name='RWR Accounts Stats', url='rwr-accounts-stats'))
admin.add_view(RestrictedModelView(models.User, db.session, name='Users', url='users'))
admin.add_view(RestrictedModelView(models.UserFriend, db.session, name='Users Friends', url='users-friends'))
admin.add_view(RestrictedModelView(models.Variable, db.session, name='Variables', url='variables'))
