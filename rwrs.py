from flask_discord_interactions import DiscordInteractions
from flask_login import LoginManager, current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, AdminIndexView
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_openid import OpenID
from flask_caching import Cache
from flask import Flask, abort
import math


# -----------------------------------------------------------
# App bootstrap


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

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

# Flask-HTMLmin
try:
    from flask_htmlmin import HTMLMIN

    htmlmin = HTMLMIN(app)
except ImportError:
    pass

# Flask-SQLAlchemy
db = SQLAlchemy(app)

# Flask-Migrate
migrate = Migrate(app, db)

# Flask-Caching
cache = Cache(app)

# Flask-Assets
assets = Environment(app)

assets.register('js_popovers', Bundle('js/popovers.js', filters='jsmin', output='js/popovers.min.js'))
assets.register('js_popovers_rwr_accounts_sync', Bundle('js/popovers.js', 'js/rwr_accounts_sync.js', filters='jsmin', output='js/popovers_rwr_accounts_sync.min.js'))
assets.register('js_charts', Bundle('js/charts.js', filters='jsmin', output='js/charts.min.js'))
assets.register('js_charts_popovers', Bundle('js/charts.js', 'js/popovers.js', filters='jsmin', output='js/charts_popovers.min.js'))
assets.register('js_regenerate_pat', Bundle('js/regenerate_pat.js', filters='jsmin', output='js/regenerate_pat.min.js'))
assets.register('js_rwr_account_deletion', Bundle('js/rwr_account_deletion.js', filters='jsmin', output='js/rwr_account_deletion.min.js'))
assets.register('css_app', Bundle('css/flags.css', 'css/app.css', filters='cssutils', output='css/app.min.css'))

# Flask-Login
login_manager = LoginManager(app)
login_manager.login_message_category = 'info'

# Flask-OpenID
oid = OpenID(app)

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

admin = Admin(app, name='RWRS Admin', template_mode='bootstrap4', url='/manage',
              index_view=RestrictedAdminIndexView(url='/manage'))

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
# After-bootstrap imports


import models
import routes
import commands
import discord.commands
import hooks
import api

# Flask-Admin

admin.add_view(RestrictedModelView(models.RwrAccount, db.session, name='RWR Accounts', url='rwr-accounts'))
admin.add_view(RestrictedModelView(models.RwrAccountStat, db.session, name='RWR Accounts Stats', url='rwr-accounts-stats'))
admin.add_view(RestrictedModelView(models.User, db.session, name='Users', url='users'))
admin.add_view(RestrictedModelView(models.UserFriend, db.session, name='Users Friends', url='users-friends'))
admin.add_view(RestrictedModelView(models.Variable, db.session, name='Variables', url='variables'))
