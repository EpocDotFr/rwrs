from flask import render_template, abort, request, redirect, url_for, flash
from rwrs import app
from models import *
import rwr


ERROR_PLAYER_NOT_FOUND = 'Sorry, the player "{username}" wasn\'t found. Maybe this player hasn\'t already played on a ranked server yet. If this player started to play today on a ranked server, please wait until tomorrow as stats are refreshed daily.'


@app.route('/')
def home():
    online_players_data = ServerPlayerCount.server_players_data()
    servers_online_data = ServerPlayerCount.servers_data()
    servers_active_data = ServerPlayerCount.servers_data(active_only=True)

    servers_data = [
        servers_online_data,
        servers_active_data
    ]

    return render_template(
        'home.html',
        online_players_data=online_players_data,
        servers_data=servers_data
    )


@app.route('/my-friends')
def my_friends():
    return render_template(
        'manage_friends.html'
    )


@app.route('/players')
def players_list():
    return render_template('players_list.html')


@app.route('/players')
@app.route('/players/<username>')
def player_stats(username=None):
    if not username:
        username = request.args.get('username').strip()

        # Redirect to a SEO-friendly URL if the username query parameter is detected
        return redirect(url_for('player_stats', username=username), code=301)

    if not username:
        abort(404)

    scraper = rwr.DataScraper()

    player = scraper.search_player(username)

    if not player:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=username), 'error')

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
        return redirect(url_for('players_compare', username=username, username_to_compare_with=username_to_compare_with), code=301)

    if not username_to_compare_with:
        abort(404)

    scraper = rwr.DataScraper()

    player = scraper.search_player(username)

    if not player:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=username), 'error')

        return redirect(url_for('home'))

    player_to_compare_with = scraper.search_player(username_to_compare_with)

    if not player_to_compare_with:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=username_to_compare_with), 'error')

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

    port = int(port)

    scraper = rwr.DataScraper()

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
