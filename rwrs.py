try:
    from flask_debugtoolbar import DebugToolbarExtension

    has_debug_toolbar_ext = True
except ImportError:
    has_debug_toolbar_ext = False

from flask_assets import Environment, Bundle
from bugsnag.flask import handle_exceptions
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_openid import OpenID
from flask_caching import Cache
from flask import Flask
import bugsnag
import math


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

import helpers

app.config['SQLALCHEMY_DATABASE_URI'] = helpers.build_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'storage/cache'
app.config['RANKS_IMAGES_DIR'] = 'static/images/ranks'
app.config['RANKS_DATA_FILE'] = 'storage/data/ranks.json'
app.config['MINIMAPS_IMAGES_DIR'] = 'static/images/maps/minimap'
app.config['MAPS_PREVIEW_IMAGES_DIR'] = 'static/images/maps/preview'
app.config['MAPS_DATA_FILE'] = 'storage/data/maps.json'
app.config['ITEMS_DATA_FILE'] = 'storage/data/items.json'
app.config['GEOIP_DATABASE_FILE'] = 'storage/data/GeoLite2-City.mmdb'
app.config['RANKED_SERVERS_ADMINS_FILE'] = 'storage/data/ranked_servers_admins.json'
app.config['MY_USERNAME'] = 'epocdotfr'
app.config['CONTRIBUTORS'] = ['street veteran', 'mastock', 'dio', 'jatimatik', 'mellcor', 'teratai', 'harrified', 'mr. bang', 'dogtato']
app.config['DEVS'] = ['jackmayol', 'pasik', 'pasik2', 'tremozl', 'the soldier', '577']
app.config['LIST_PAGE_SIZES'] = [15, 30, 50, 100]
app.config['RWR_STEAM_APP_ID'] = 270150
app.config['BUNDLE_ERRORS'] = True

if app.config['ENV'] == 'production' and app.config['BUGSNAG_API_KEY']:
    bugsnag.configure(
        api_key=app.config['BUGSNAG_API_KEY']
    )

    handle_exceptions(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(app)
assets = Environment(app)
login_manager = LoginManager(app)
oid = OpenID(app)

if has_debug_toolbar_ext:
    toolbar = DebugToolbarExtension(app)

assets.cache = 'storage/webassets-cache/'

assets.register('js_friends', Bundle('js/common.js', 'js/friends.js', filters='jsmin', output='js/friends.min.js'))
assets.register('js_friends_popovers', Bundle('js/common.js', 'js/friends.js', 'js/popovers.js', filters='jsmin', output='js/friends_popover.min.js'))
assets.register('js_friends_charts', Bundle('js/common.js', 'js/friends.js', 'js/charts.js', filters='jsmin', output='js/friends_charts.min.js'))
assets.register('js_friends_charts_popovers', Bundle('js/common.js', 'js/friends.js', 'js/charts.js', 'js/popovers.js', filters='jsmin', output='js/friends_charts_popover.min.js'))
assets.register('js_friends_player_claim', Bundle('js/common.js', 'js/friends.js', 'js/player_claim.js', filters='jsmin', output='js/friends_player_claim.min.js'))
assets.register('css_app', Bundle('css/flags.css', 'css/app.css', filters='cssutils', output='css/app.min.css'))

login_manager.session_protection = 'strong'
login_manager.login_message_category = 'info'

import rwr.constants
import rwr.utils

app.config['RANKED_SERVERS_ADMINS'] = helpers.load_json(app.config['RANKED_SERVERS_ADMINS_FILE'])

app.jinja_env.filters.update(
    humanize_seconds_to_days=helpers.humanize_seconds_to_days,
    humanize_seconds_to_hours=helpers.humanize_seconds_to_hours,
    humanize_integer=helpers.humanize_integer,
    simplified_integer=helpers.simplified_integer
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
    PLAYERS_LIST_DATABASES=rwr.constants.PLAYERS_LIST_DATABASES
)


# -----------------------------------------------------------
# After-init imports


import models
import routes
import commands
import hooks
import api
