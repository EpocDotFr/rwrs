from werkzeug.exceptions import HTTPException, Unauthorized, Forbidden, NotFound, InternalServerError, ServiceUnavailable
from flask import Flask, redirect, flash, url_for, request, g, abort, render_template, Markup
from flask_login import LoginManager, current_user, login_user
from flask_discord_interactions import DiscordInteractions
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, AdminIndexView
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_openid import OpenID
from flask_caching import Cache
from rwrs import helpers, motd
from datetime import datetime
from environs import Env
import arrow
import math
import os

# -----------------------------------------------------------
# App bootstrap

env = Env()
env.read_env()

app = Flask(__name__)

app.config.update(
    # Default config values that may be overwritten by environment values
    SECRET_KEY=env.str('SECRET_KEY'),
    SERVER_NAME=env.str('SERVER_NAME', default='localhost:8080'),
    PREFERRED_URL_SCHEME=env.str('PREFERRED_URL_SCHEME', default='http'),

    SENTRY_DSN=env.str('SENTRY_DSN', default=None),
    SENTRY_TRACES_SAMPLE_RATE=env.float('SENTRY_TRACES_SAMPLE_RATE', default=None),

    CACHE_TYPE=env.str('CACHE_TYPE', default='FileSystemCache'),
    CACHE_DIR=env.str('CACHE_DIR', default='instance/cache'),

    ASSETS_CACHE=env.str('ASSETS_CACHE', default='instance/webassets-cache'),

    DEBUG_TB_INTERCEPT_REDIRECTS=env.bool('DEBUG_TB_INTERCEPT_REDIRECTS', False),

    MINIFY_HTML=env.bool('MINIFY_HTML', default=False),

    COMPRESS_REGISTER=env.bool('COMPRESS_REGISTER', default=False),
    COMPRESS_MIN_SIZE=env.int('COMPRESS_MIN_SIZE', 512),

    SQLALCHEMY_DATABASE_URI=env.str('SQLALCHEMY_DATABASE_URI', default='sqlite:///instance/db.sqlite'),

    SERVERS_CACHE_TIMEOUT=env.int('SERVERS_CACHE_TIMEOUT', default=60),
    PLAYERS_CACHE_TIMEOUT=env.int('PLAYERS_CACHE_TIMEOUT', default=60),
    GRAPHS_DATA_CACHE_TIMEOUT=env.int('GRAPHS_DATA_CACHE_TIMEOUT', default=60),
    STEAM_PLAYERS_CACHE_TIMEOUT=env.int('STEAM_PLAYERS_CACHE_TIMEOUT', default=60),

    STEAM_API_KEY=env.str('STEAM_API_KEY'),

    MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR=env.int('MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR', default=1000),

    DISCORD_CLIENT_ID=env.str('DISCORD_CLIENT_ID'),
    DISCORD_PUBLIC_KEY=env.str('DISCORD_PUBLIC_KEY'),
    DISCORD_CLIENT_SECRET=env.str('DISCORD_CLIENT_SECRET'),
    DISCORD_GUILD=env.str('DISCORD_GUILD'),

    RWR_ACCOUNTS_ENDPOINTS_CREDENTIALS=tuple(env.list('RWR_ACCOUNTS_ENDPOINTS_CREDENTIALS', ['username', 'password'])),

    RWR_ACCOUNTS_BY_STEAM_ID_ENDPOINT=env.str('RWR_ACCOUNTS_BY_STEAM_ID_ENDPOINT', default=None),
    RWR_ACCOUNTS_DELETE_ENDPOINT=env.str('RWR_ACCOUNTS_DELETE_ENDPOINT', default=None),

    ADMINS=env.list('ADMINS', default=[]),

    SCRAPER_PROXY=env.str('SCRAPER_PROXY', default=None),

    # Config values that cannot be overwritten
    CACHE_THRESHOLD=10000,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    BUNDLE_ERRORS=True,
    SESSION_PROTECTION='basic',

    RANKS_IMAGES_DIR='static/images/ranks',
    RANKS_DATA_FILE='data/ranks.json',

    MINIMAPS_IMAGES_DIR='static/images/maps/minimap',
    MAPS_PREVIEW_IMAGES_DIR='static/images/maps/preview',
    MAPS_DATA_FILE= 'data/maps.json',

    GEOIP_DATABASE_FILE='instance/GeoLite2-City.mmdb',

    OFFICIAL_SERVERS_MODS_FILE='data/official_servers_mods.json',

    MY_USERNAME='epocdotfr',
    CONTRIBUTORS=['street veteran', 'mastock', 'dio', 'jatimatik', 'mellcor', 'teratai', 'harrified', 'mr. bang',
                  'dogtato', 'stesmith', 'korgorr', 'foxtrod', 'moorsey100', 'moorsey the owl', 'kilroy (7kb/s)'],
    DEVS=['jackmayol', 'pasik', 'pasik2', 'tremozl', 'the soldier', '577', 'unit g17'],

    LIST_PAGE_SIZES=[15, 30, 50, 100],
    RWR_STEAM_APP_ID=270150,

    EVENT_DATETIME_INPUT_FORMAT='YYYY-MM-DD HH:mm ZZ',
    EVENT_DATETIME_DISPLAY_FORMAT='MMMM Do, YYYY @ h:mm A ZZ',

    STATUS_PAGE_URL='https://stats.uptimerobot.com/Z0PkQf9YY',

    DISCORD_SERVER_URL='https://discord.gg/runningwithrifles',
    DISCORD_INTERACTIONS_PATH='/discord-interactions',
    MY_DISCORD_ID='66543750725246976',
)

app.config['OFFICIAL_SERVERS_MODS'] = helpers.load_json(app.config['OFFICIAL_SERVERS_MODS_FILE'])

# -----------------------------------------------------------
# Debugging-related behaviours

if app.config['SENTRY_DSN']:
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

assets.register('js_popovers', Bundle('js/popovers.js', filters='rjsmin', output='js/popovers.min.js'))
assets.register('js_popovers_rwr_accounts_sync', Bundle('js/popovers.js', 'js/rwr_accounts_sync.js', filters='rjsmin', output='js/popovers_rwr_accounts_sync.min.js'))
assets.register('js_charts', Bundle('js/charts.js', filters='rjsmin', output='js/charts.min.js'))
assets.register('js_charts_popovers', Bundle('js/charts.js', 'js/popovers.js', filters='rjsmin', output='js/charts_popovers.min.js'))
assets.register('js_regenerate_pat', Bundle('js/regenerate_pat.js', filters='rjsmin', output='js/regenerate_pat.min.js'))
assets.register('js_rwr_account_deletion', Bundle('js/rwr_account_deletion.js', filters='rjsmin', output='js/rwr_account_deletion.min.js'))
assets.register('css_app', Bundle('css/flags.css', 'css/app.css', filters='rcssmin', output='css/app.min.css'))

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
    from rwrs.models import User

    return User.query.get(user_id)

# Flask-OpenID
oid = OpenID(app)


@oid.after_login
def create_or_login(resp):
    from rwrs.steam_helpers import parse_steam_id_from_identity_url, get_user_summaries
    from rwrs.models import User

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
    from rwrs.steam_helpers import get_current_players_count_for_app
    from rwrs import event
    import rwr.scraper

    if request.endpoint and request.endpoint.startswith(('static', 'debugtoolbar', '_debug_toolbar')):
        return

    g.UNDER_MAINTENANCE = os.path.exists('maintenance')

    if request.endpoint and request.endpoint in ('dynamic_player_image', 'dynamic_server_image'):
        return

    g.MOTD = motd.get()
    g.EVENT = event.get()

    if request.path == app.config['DISCORD_INTERACTIONS_PATH']:
        return

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
    if isinstance(e, Unauthorized):
        page_icon = 'fas fa-minus-circle'
        title = 'Unauthorized'
        text = 'It seems you\'re not authorized to go here.'
        type = 'error'
    elif isinstance(e, Forbidden):
        page_icon = 'fas fa-minus-circle'
        title = 'Forbidden'
        text = 'Access to this resource is forbidden.'
        type = 'error'
    elif isinstance(e, NotFound):
        page_icon = 'fas fa-question'
        title = 'Not found'
        text = 'Sorry, there\'s nothing here.'
        type = 'info'
    elif isinstance(e, InternalServerError):
        page_icon = 'fas fa-exclamation-triangle'
        title = 'Server error'
        text = Markup('Whoops, a server error occurred! Please retry. If the error persists, please <a href="{}">get in touch</a>.'.format(url_for('feedback')))
        type = 'error'
    elif isinstance(e, ServiceUnavailable):
        page_icon = 'fas fa-wrench'
        title = 'Unavailable'
        text = Markup('Sorry, RWRS is temporarily unavailable <i class="fa fa-frown"></i><br><br>{}')

        if g.MOTD:
            text = text.format(helpers.markdown_to_html_inline(g.MOTD.message))
            type = g.MOTD.type
        else:
            text = text.format('There is an ongoing maintenance, please check back later.')
            type = 'info'
    else:
        page_icon = 'fas fa-exclamation-triangle'
        title = e.name
        text = e.description
        type = 'error'

    return render_template(
        'error.html',
        page_icon=page_icon,
        title=title,
        text=text,
        type=type,
    ), e.code

# -----------------------------------------------------------
# After-bootstrap imports

import rwrs.models
import rwrs.routes
import rwrs.commands
import rwrs.discord.commands
import rwrs.api

admin.add_view(RestrictedModelView(rwrs.models.RwrAccount, db.session, name='RWR Accounts', url='rwr-accounts'))
admin.add_view(RestrictedModelView(rwrs.models.RwrAccountStat, db.session, name='RWR Accounts Stats', url='rwr-accounts-stats'))
admin.add_view(RestrictedModelView(rwrs.models.User, db.session, name='Users', url='users'))
admin.add_view(RestrictedModelView(rwrs.models.UserFriend, db.session, name='Users Friends', url='users-friends'))
admin.add_view(RestrictedModelView(rwrs.models.Variable, db.session, name='Variables', url='variables'))
