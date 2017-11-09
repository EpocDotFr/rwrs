from flask import Flask, render_template, make_response, abort, request, redirect, url_for, flash, g
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import ArrowType, IPAddressType
from flask_caching import Cache
from helpers import *
import logging
import arrow
import click
import math
import sys
import os


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage/data/db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'storage/cache'
app.config['RANKS_IMAGES_DIR'] = 'static/images/ranks'
app.config['MINIMAPS_IMAGES_DIR'] = 'static/images/maps/minimap'
app.config['UNLOCKABLES_IMAGES_DIR'] = 'static/images/unlockables'
app.config['MY_USERNAME'] = 'epocdotfr'
app.config['CONTRIBUTORS'] = ['street veteran', 'mastock']
app.config['DEVS'] = ['jackmayol', 'pasik', 'pasik2', 'tremozl', 'the soldier'] # ahnold

app.jinja_env.filters.update(
    humanize_seconds=humanize_seconds,
    humanize_integer=humanize_integer
)

app.jinja_env.globals.update(
    int=int,
    float=float,
    str=str,
    round=round,
    abs=abs,
    fabs=math.fabs,
    isinstance=isinstance
)

db = SQLAlchemy(app)
cache = Cache(app)

# Default Python logger
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    stream=sys.stdout
)

logging.getLogger().setLevel(logging.INFO)

# Default Flask loggers
for handler in app.logger.handlers:
    handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S'))


# -----------------------------------------------------------
# After-init imports


import rwr


# -----------------------------------------------------------
# Routes


@app.route('/')
def home():
    return render_template(
        'home.html'
    )


@app.route('/my-friends')
def my_friends():
    return render_template(
        'manage_friends.html'
    )


@app.route('/players')
@app.route('/players/<username>')
def player_stats(username=None):
    if not username:
        username = request.args.get('username').strip()

        # Redirect to a SEO-friendly URL if the username query parameter is detected
        return redirect(url_for('player_stats', username=username))

    if not username:
        abort(404)

    scraper = rwr.DataScraper()

    player = scraper.search_player(username)

    if not player:
        flash('Sorry, the player "{}" wasn\'t found. Maybe this player hasn\'t already played on a ranked server yet.'.format(username), 'error')

        return redirect(url_for('home'))

    servers = scraper.get_servers()

    player.set_playing_on_server(servers)

    return render_template(
        'player_stats.html',
        player=player
    )


@app.route('/players/<username>/compare')
@app.route('/players/<username>/compare/<username_to_compare_with>')
def players_compare(username, username_to_compare_with=None):
    if not username_to_compare_with:
        username_to_compare_with = request.args.get('username_to_compare_with').strip()

        # Redirect to a SEO-friendly URL if the username_to_compare_with query parameter is detected
        return redirect(url_for('players_compare', username=username, username_to_compare_with=username_to_compare_with))

    if not username_to_compare_with:
        abort(404)

    scraper = rwr.DataScraper()

    player = scraper.search_player(username)

    if not player:
        flash('Sorry, the player "{}" wasn\'t found. Maybe this player hasn\'t already played on a ranked server yet.'.format(username), 'error')

        return redirect(url_for('home'))

    player_to_compare_with = scraper.search_player(username_to_compare_with)

    if not player_to_compare_with:
        flash('Sorry, the player "{}" wasn\'t found. Maybe this player hasn\'t already played on a ranked server yet.'.format(username_to_compare_with), 'error')

        return redirect(url_for('player_stats', username=username))

    servers = scraper.get_servers()

    player.set_playing_on_server(servers)

    return render_template(
        'player_stats.html',
        player=player,
        player_to_compare_with=player_to_compare_with
    )


@app.route('/servers')
def servers_list():
    scraper = rwr.DataScraper()

    filters = request.args.to_dict()

    if filters:
        servers = scraper.filter_servers(**filters)
    else:
        servers = scraper.get_servers()

    locations = scraper.get_all_servers_locations()
    types = scraper.get_all_servers_types()
    modes = scraper.get_all_servers_modes()
    maps = scraper.get_all_servers_maps()

    return render_template(
        'servers_list.html',
        servers=servers,
        locations=locations,
        types=types,
        modes=modes,
        maps=maps
    )


@app.route('/servers/<ip_and_port>')
def server_details(ip_and_port):
    ip, port = ip_and_port.split(':', maxsplit=1)

    scraper = rwr.DataScraper()

    server = scraper.search_server(ip, int(port))

    if not server:
        flash('Sorry, this server wasn\'t found.', 'error')

        return redirect(url_for('servers_list'))

    return render_template(
        'server_details.html',
        server=server
    )


# -----------------------------------------------------------
# Models


class ServerPlayersCount(db.Model):
    __tablename__ = 'server_players_counts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    ip = db.Column(IPAddressType, nullable=False)
    port = db.Column(db.Integer, nullable=False)
    datetime = db.Column(ArrowType, default=arrow.utcnow())
    count = db.Column(db.Integer, nullable=False)

    def __init__(self, ip=None, port=None, datetime=arrow.utcnow(), count=None):
        self.ip = ip
        self.port = port
        self.datetime = datetime
        self.count = count

    def __repr__(self):
        return '<ServerPlayersCount> #{}'.format(self.id)


# -----------------------------------------------------------
# CLI commands


@app.cli.command()
def create_database():
    """Delete then create all the database tables."""
    db.drop_all()
    db.create_all()


@app.cli.command()
def seed_database():
    """Seed the DB with fake data."""
    import random

    try:
        from faker import Faker
    except ImportError:
        logging.error('Faker is required for this action.')

        return

    fake = Faker()

    server_ips = [fake.ipv4() for i in range(0, 30)]
    server_ports = [random.randint(1234, 5678) for i in range(0, 6)]

    for server_ip in server_ips:
        spc = ServerPlayersCount()
        spc.ip = server_ip
        spc.port = random.choice(server_ports)
        spc.count = random.randint(0, 24)

        db.session.add(spc)

    db.session.commit()

@app.cli.command()
@click.option('--gamedir', '-g', help='Game root directory')
def extract_ranks_images(gamedir):
    """Extract ranks images from RWR."""
    context = click.get_current_context()

    if not gamedir:
        click.echo(extract_ranks_images.get_help(context))
        context.exit()

    app.logger.info('Extraction started')

    extractor = rwr.RanksImageExtractor(gamedir, app.config['RANKS_IMAGES_DIR'])
    extractor.extract()

    app.logger.info('Done')


@app.cli.command()
@click.option('--gamedir', '-g', help='Game root directory')
def extract_minimaps(gamedir):
    """Extract minimaps from RWR."""
    context = click.get_current_context()

    if not gamedir:
        click.echo(extract_minimaps.get_help(context))
        context.exit()

    app.logger.info('Extraction started')

    extractor = rwr.MinimapsImageExtractor(gamedir, app.config['MINIMAPS_IMAGES_DIR'])
    extractor.extract()

    app.logger.info('Done')


# -----------------------------------------------------------
# HTTP errors handler


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

    g.INCLUDE_WEB_ANALYTICS = False
    g.NO_INDEX = True

    body = render_template('errors/{}.html'.format(error))

    if not without_code:
        return make_response(body, error)
    else:
        return make_response(body)


# -----------------------------------------------------------
# Hooks


@app.before_request
def define_globals():
    scraper = rwr.DataScraper()

    g.all_players_with_servers_details = scraper.get_all_players_with_servers_details()

    online_players, active_servers, total_servers = scraper.get_counters()

    g.online_players = online_players
    g.active_servers = active_servers
    g.total_servers = total_servers

    g.INCLUDE_WEB_ANALYTICS = not app.config['DEBUG']
    g.NO_INDEX = False


@app.url_defaults
def hashed_static_file(endpoint, values):
    """Add a cache-buster value in the URL of each static assets."""
    if endpoint == 'static':
        filename = values.get('filename')

        if filename:
            blueprint = request.blueprint

            if '.' in endpoint:
                blueprint = endpoint.rsplit('.', 1)[0]

            static_folder = app.static_folder

            if blueprint and app.blueprints[blueprint].static_folder:
                static_folder = app.blueprints[blueprint].static_folder

            fp = os.path.join(static_folder, filename)

            if os.path.exists(fp):
                values[int(os.stat(fp).st_mtime)] = ''
