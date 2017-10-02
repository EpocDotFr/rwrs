from flask import Flask, render_template, make_response, abort, request, redirect, url_for, flash
from werkzeug.exceptions import HTTPException
import rwr_scrapers
import logging
import sys
import math
import click


# -----------------------------------------------------------
# Helpers


def humanize_seconds(seconds):
    """Return a human-readable representation of the given number of seconds."""
    if not seconds:
        return ''

    d = int(seconds / (60 * 60 * 24))
    h = int((seconds % (60 * 60 * 24)) / (60 * 60))
    m = int((seconds % (60 * 60)) / 60)
    s = int(seconds % 60)

    ret = []

    if d:
        ret.append(('{}d', d))

    if h:
        ret.append(('{}h', h))

    if m:
        ret.append(('{:>02}m', m))

    if s:
        ret.append(('{:>02}s', s))

    f, v = zip(*ret)

    return ' '.join(f).format(*v)


def humanize_integer(integer):
    """Return a slightly more human-readable representation of the given integer."""
    if not integer:
        return 0

    return format(integer, ',d').replace(',', ' ')


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

app.config['RANKS_IMAGES_DIR'] = 'static/images/ranks'
app.config['MINIMAPS_IMAGES_DIR'] = 'static/images/maps/minimap'

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
    fabs=math.fabs
)

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
# Routes


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/players')
@app.route('/players/<username>')
def player_stats(username=None):
    if not username:
        username = request.args.get('username')

        # Redirect to a SEO-friendly URL if the username query parameter is detected
        return redirect(url_for('player_stats', username=username))

    if not username:
        abort(404)

    scraper = rwr_scrapers.DataScraper()

    player = scraper.search_player(username)

    if not player:
        flash('Sorry, the player "{}" wasn\'t found.'.format(username), 'error')

        return redirect(url_for('home'))

    servers = scraper.get_servers()

    player.set_playing_on_server(servers)

    return render_template('player_stats.html', player=player)


@app.route('/players/<username>/compare')
@app.route('/players/<username>/compare/<username_to_compare_with>')
def players_compare(username, username_to_compare_with=None):
    if not username_to_compare_with:
        username_to_compare_with = request.args.get('username_to_compare_with')

        # Redirect to a SEO-friendly URL if the username_to_compare_with query parameter is detected
        return redirect(url_for('players_compare', username=username, username_to_compare_with=username_to_compare_with))

    if not username_to_compare_with:
        abort(404)

    scraper = rwr_scrapers.DataScraper()

    player = scraper.search_player(username)

    if not player:
        flash('Sorry, the player "{}" wasn\'t found.'.format(username), 'error')

        return redirect(url_for('home'))

    player_to_compare_with = scraper.search_player(username_to_compare_with)

    if not player_to_compare_with:
        flash('Sorry, the player "{}" wasn\'t found.'.format(username_to_compare_with), 'error')

        return redirect(url_for('player_stats', username=username))

    servers = scraper.get_servers()

    player.set_playing_on_server(servers)

    return render_template('player_stats.html', player=player, player_to_compare_with=player_to_compare_with)


@app.route('/servers')
def servers_list():
    scraper = rwr_scrapers.DataScraper()

    return render_template('servers_list.html', servers=scraper.get_servers())


@app.route('/servers/<ip_and_port>')
def server_details(ip_and_port):
    ip, port = ip_and_port.split(':', maxsplit=1)

    scraper = rwr_scrapers.DataScraper()

    server = scraper.search_server(ip, port)

    if not server:
        flash('Sorry, this server wasn\'t found.', 'error')

        return redirect(url_for('servers_list'))

    return render_template('server_details.html', server=server)


# -----------------------------------------------------------
# CLI commands


@app.cli.command()
def download_ranks_images():
    """Download and save all the ranks images."""
    app.logger.info('Starting download')

    scraper = rwr_scrapers.RanksImageScraper(app.config['RANKS_IMAGES_DIR'])
    scraper.run()

    app.logger.info('Done')


@app.cli.command()
@click.option('--gamedir', '-g', help='Game root directory')
def extract_minimaps(gamedir):
    """Extract minimaps from RWR."""
    context = click.get_current_context()

    if not gamedir:
        click.echo(extract_minimaps.get_help(context))
        context.exit()

    app.logger.info('Extracting started')

    extractor = rwr_scrapers.MinimapsImageExtractor(gamedir, app.config['MINIMAPS_IMAGES_DIR'])
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

    body = render_template('errors/{}.html'.format(error))

    if not without_code:
        return make_response(body, error)
    else:
        return make_response(body)
