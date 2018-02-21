from logging.handlers import RotatingFileHandler
from flask_assets import Environment, Bundle
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask import Flask
import logging
import math


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

app.config['LOGGER_HANDLER_POLICY'] = 'production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage/data/db.sqlite'
app.config['SQLALCHEMY_BINDS'] = {
    'servers_player_count': 'sqlite:///storage/data/servers_player_count.sqlite',
    'steam_players_count': 'sqlite:///storage/data/steam_players_count.sqlite'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'storage/cache'
app.config['RANKS_IMAGES_DIR'] = 'static/images/ranks'
app.config['RANKS_DATA_FILE'] = 'storage/data/ranks.json'
app.config['MINIMAPS_IMAGES_DIR'] = 'static/images/maps/minimap'
app.config['MAPS_PREVIEW_IMAGES_DIR'] = 'static/images/maps/preview'
app.config['MAPS_DATA_FILE'] = 'storage/data/maps.json'
app.config['UNLOCKABLES_IMAGES_DIR'] = 'static/images/unlockables'
app.config['UNLOCKABLES_DATA_FILE'] = 'storage/data/unlockables.json'
app.config['MY_USERNAME'] = 'epocdotfr'
app.config['CONTRIBUTORS'] = ['street veteran', 'mastock', 'dio']
app.config['DEVS'] = ['jackmayol', 'pasik', 'pasik2', 'tremozl', 'the soldier'] # ahnold
app.config['PLAYERS_LIST_PAGE_SIZES'] = [15, 30, 50, 100]
app.config['RWR_STEAM_APP_ID'] = 270150

db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(app)
auth = HTTPBasicAuth()
assets = Environment(app)

assets.cache = 'storage/webassets-cache/'

assets.register('js_friends_charts', Bundle('js/common.js', 'js/friends.js', 'js/charts.js', filters='jsmin', output='js/friends_charts.min.js'))
assets.register('js_friends_status', Bundle('js/common.js', 'js/friends.js', 'js/status.js', filters='jsmin', output='js/friends_status.min.js'))
assets.register('js_friends', Bundle('js/common.js', 'js/friends.js', filters='jsmin', output='js/friends.min.js'))
assets.register('css_app', Bundle('css/flags.css', 'css/app.css', filters='cssutils', output='css/app.min.css'))

handler = RotatingFileHandler('storage/logs/errors.log', maxBytes=10000000, backupCount=2)
handler.setLevel(logging.WARNING)
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

import helpers
import rwr.constants
import rwr.utils

app.jinja_env.filters.update(
    humanize_seconds_to_days=helpers.humanize_seconds_to_days,
    humanize_seconds_to_hours=helpers.humanize_seconds_to_hours,
    humanize_integer=helpers.humanize_integer
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


import routes
import models
import commands
import hooks
