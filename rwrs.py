from flask import Flask, render_template, make_response, abort
from werkzeug.exceptions import HTTPException
import rwr_scrapers
import logging
import sys


# -----------------------------------------------------------
# Boot


app = Flask(__name__, static_url_path='')
app.config.from_pyfile('config.py')

app.config['RANKS_IMAGES_DIR'] = 'static/images/ranks'

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


@app.route('/player/<username>')
def player_stats(username):
    scraper = rwr_scrapers.DataScraper()

    player = scraper.search_player(username)

    if not player:
        abort(404)

    return render_template('player_stats.html', player=player)


@app.route('/servers')
def servers_list():
    scraper = rwr_scrapers.DataScraper()

    return render_template('servers_list.html', servers=scraper.get_servers())


# -----------------------------------------------------------
# CLI commands


@app.cli.command()
def download_ranks_images():
    """Download and save all the ranks images."""
    app.logger.info('Starting download')

    scraper = rwr_scrapers.RanksImageScraper(app.config['RANKS_IMAGES_DIR'])
    scraper.run()

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
