from flask import render_template, abort, request, redirect, url_for, flash, g
from rwrs import app
from models import *
import rwr.constants
import rwr.scraper
import rwr.utils


ERROR_PLAYER_NOT_FOUND = 'Sorry, the player "{username}" wasn\'t found in the {database} players list. Maybe this player hasn\'t already played on a ranked server yet. If this player started to play today on a ranked server, please wait until tomorrow as stats are refreshed daily.'


@app.route('/')
def home():
    total_players_data = SteamPlayerCount.players_data()
    online_players_data = ServerPlayerCount.server_players_data()
    servers_online_data = ServerPlayerCount.servers_data()
    servers_active_data = ServerPlayerCount.servers_data(active_only=True)

    players_data = [
        total_players_data,
        online_players_data
    ]

    servers_data = [
        servers_online_data,
        servers_active_data
    ]

    return render_template(
        'home.html',
        players_data=players_data,
        servers_data=servers_data
    )


@app.route('/my-friends')
def my_friends():
    return render_template(
        'manage_friends.html'
    )


@app.route('/online-status')
def online_status():
    return render_template(
        'online_status.html',
        servers_to_monitor=rwr.constants.SERVERS_TO_MONITOR
    )


@app.route('/players')
def players_list_without_db():
    database = request.args.get('database', 'invasion')
    username = request.args.get('username')

    if username:
        username = username.strip()

        # Redirect to a SEO-friendly URL if the username query parameter is detected
        return redirect(url_for('player_details', database=database, username=username), code=301)

    return redirect(url_for('players_list', database=database), code=301)


@app.route('/players/<any(' + ','.join(rwr.constants.PLAYERS_LIST_DATABASES.keys()) + '):database>')
def players_list(database):
    args = request.args.to_dict()

    args['sort'] = args.get('sort', rwr.constants.PlayersSort.SCORE)

    if not args.get('limit') or int(args.get('limit')) > app.config['PLAYERS_LIST_PAGE_SIZES'][-1]:
        args['limit'] = app.config['PLAYERS_LIST_PAGE_SIZES'][0]
    else:
        args['limit'] = int(args.get('limit'))

    if args.get('target'):
        args['target'] = args.get('target').upper()

    scraper = rwr.scraper.DataScraper()

    servers = scraper.get_servers()

    players = scraper.get_players(
        database,
        sort=args['sort'],
        target=args['target'] if args.get('target') else None,
        start=args['start'] if args.get('start') else None,
        limit=args['limit']
    )

    target_found = False

    for player in players:
        player.set_playing_on_server(servers)

        if args.get('target') and player.username == args.get('target'):
            target_found = True

    if args.get('target') and not target_found:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=args.get('target'), database=rwr.utils.get_database_name(database)), 'error')

        return redirect(url_for('players_list', database=database))

    g.LAYOUT = 'large'

    return render_template(
        'players_list.html',
        players=players,
        args=args
    )


@app.route('/players/<username>')
def player_details_without_db(username):
    return redirect(url_for('player_details', database='invasion', username=username), code=301)


@app.route('/players/<any(' + ','.join(rwr.constants.PLAYERS_LIST_DATABASES.keys()) + '):database>/<username>')
@app.route('/players/<any(' + ','.join(rwr.constants.PLAYERS_LIST_DATABASES.keys()) + '):database>/<username>/<any(unlockables):tab>')
def player_details(database, username, tab=None):
    scraper = rwr.scraper.DataScraper()

    player = scraper.search_player(database, username)

    if not player:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=username, database=rwr.utils.get_database_name(database)), 'error')

        return redirect(url_for('players_list', database=database))

    servers = scraper.get_servers()

    player.set_playing_on_server(servers)

    return render_template(
        'player_details/main.html',
        player=player
    )


@app.route('/players/<username>/compare')
@app.route('/players/<username>/compare/<username_to_compare_with>')
def players_compare_without_db(username, username_to_compare_with=None):
    if not username_to_compare_with and request.args.get('username_to_compare_with'):
        username_to_compare_with = request.args.get('username_to_compare_with').strip()

    return redirect(url_for('players_compare', database='invasion', username=username, username_to_compare_with=username_to_compare_with), code=301)


@app.route('/players/<any(' + ','.join(rwr.constants.PLAYERS_LIST_DATABASES.keys()) + '):database>/<username>/compare')
@app.route('/players/<any(' + ','.join(rwr.constants.PLAYERS_LIST_DATABASES.keys()) + '):database>/<username>/compare/<username_to_compare_with>')
def players_compare(database, username, username_to_compare_with=None):
    if not username_to_compare_with and request.args.get('username_to_compare_with'):
        username_to_compare_with = request.args.get('username_to_compare_with').strip()

        # Redirect to a SEO-friendly URL if the username_to_compare_with query parameter is detected
        return redirect(url_for('players_compare', database=database, username=username, username_to_compare_with=username_to_compare_with), code=301)

    if not username_to_compare_with:
        abort(404)

    scraper = rwr.scraper.DataScraper()

    player = scraper.search_player(database, username)

    if not player:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=username, database=rwr.utils.get_database_name(database)), 'error')

        return redirect(url_for('players_list', database=database))

    player_to_compare_with = scraper.search_player(database, username_to_compare_with)

    if not player_to_compare_with:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=username_to_compare_with, database=rwr.utils.get_database_name(database)), 'error')

        return redirect(url_for('player_details', database=database, username=username))

    servers = scraper.get_servers()

    player.set_playing_on_server(servers)

    return render_template(
        'player_details/main.html',
        player=player,
        player_to_compare_with=player_to_compare_with
    )


@app.route('/servers')
def servers_list():
    scraper = rwr.scraper.DataScraper()

    filters = request.args.to_dict()

    if filters:
        servers = scraper.filter_servers(**filters)
    else:
        servers = scraper.get_servers()

    locations = scraper.get_all_servers_locations()
    types = scraper.get_all_servers_types()
    modes = scraper.get_all_servers_modes()
    maps = scraper.get_all_servers_maps()

    if request.args.get('view') == 'extended':
        g.LAYOUT = 'large'

    return render_template(
        'servers_list.html',
        servers=servers,
        locations=locations,
        types=types,
        modes=modes,
        maps=maps
    )


@app.route('/servers/<ip>:<int:port>')
def server_details_without_slug(ip, port):
    scraper = rwr.scraper.DataScraper()

    server = scraper.search_server(ip, port)

    if not server:
        flash('Sorry, this server wasn\'t found.', 'error')

        return redirect(url_for('servers_list'))

    return redirect(server.link, code=301)


@app.route('/servers/<ip>:<int:port>/<slug>')
def server_details(ip, port, slug):
    scraper = rwr.scraper.DataScraper()

    server = scraper.search_server(ip, port)

    if not server:
        flash('Sorry, this server wasn\'t found.', 'error')

        return redirect(url_for('servers_list'))

    server_players_data = ServerPlayerCount.server_players_data(ip, port) if server.is_dedicated else None

    return render_template(
        'server_details.html',
        server_players_data=server_players_data,
        server=server
    )
