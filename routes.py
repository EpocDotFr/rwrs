from models import SteamPlayerCount, ServerPlayerCount, RwrRootServer, Variable, RwrAccountStat, RwrAccount
from flask import render_template, abort, request, redirect, url_for, flash, g
from dynamic_image import DynamicServerImage, DynamicPlayerImage
from rwr.player import Player
from rwrs import app
import rwr.constants
import rwr.scraper
import rwr.utils
import arrow


ERROR_PLAYER_NOT_FOUND = 'Sorry, the player "{username}" wasn\'t found in the {database} players list. Maybe this player hasn\'t already played on a ranked server yet. If this player started to play today on a ranked server, please wait until tomorrow as stats are refreshed daily.'
ERROR_NO_RWR_ACCOUNT = 'Sorry, stats history isn\'t recorded for {username}. He/she must be part of the {database} {max_players} most experienced players.'
ERROR_NO_RWR_ACCOUNT_STATS = 'No stats were found for the given date for {username}. Are you sure he/she is/was part of the {database} {max_players} most experienced players?'

VALID_DATABASES_STRING_LIST = ','.join(rwr.constants.VALID_DATABASES)


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

    peaks = Variable.get_peaks_for_display()

    return render_template(
        'home.html',
        players_data=players_data,
        servers_data=servers_data,
        peaks=peaks
    )


@app.route('/my-friends')
def my_friends():
    return render_template(
        'manage_friends.html'
    )


@app.route('/about')
def about():
    return render_template(
        'about.html'
    )


@app.route('/feedback')
def feedback():
    return render_template(
        'feedback.html'
    )


@app.route('/online-multiplayer-status')
def online_multiplayer_status():
    is_everything_ok, servers_statuses = RwrRootServer.get_data_for_display()

    last_root_rwr_servers_check = Variable.get_value('last_root_rwr_servers_check')
    next_root_rwr_servers_check = last_root_rwr_servers_check.shift(minutes=app.config['ROOT_RWR_SERVERS_CHECK_INTERVAL']) if last_root_rwr_servers_check else None

    return render_template(
        'online_multiplayer_status.html',
        is_everything_ok=is_everything_ok,
        servers_statuses=servers_statuses,
        next_root_rwr_servers_check=next_root_rwr_servers_check
    )


@app.route('/players')
def players_list_without_db():
    database = request.args.get('database', 'invasion')
    username = request.args.get('username')

    if username:
        username = username.strip().upper()

        # Redirect to a SEO-friendly URL if the username query parameter is detected
        return redirect(url_for('player_details', database=database, username=username), code=301)

    return redirect(url_for('players_list', database=database), code=301)


@app.route('/players/<any({}):database>'.format(VALID_DATABASES_STRING_LIST))
def players_list(database):
    args = request.args.to_dict()

    args['sort'] = args.get('sort', rwr.constants.PlayersSort.SCORE)

    if not args.get('limit') or int(args.get('limit')) > app.config['LIST_PAGE_SIZES'][-1]:
        args['limit'] = app.config['LIST_PAGE_SIZES'][0]
    else:
        args['limit'] = int(args.get('limit'))

    if args.get('target'):
        args['target'] = args.get('target').upper()

    players = rwr.scraper.get_players(
        database,
        sort=args['sort'],
        target=args['target'] if args.get('target') else None,
        start=int(args['start']) if args.get('start') else 0,
        limit=args['limit']
    )

    if args.get('target') and not players:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=args.get('target'), database=rwr.utils.get_database_name(database)), 'error')

        return redirect(url_for('players_list', database=database))

    servers = rwr.scraper.get_servers()

    for player in players:
        player.set_playing_on_server(servers)

    g.LAYOUT = 'large'

    return render_template(
        'players/list.html',
        players=players,
        args=args
    )


@app.route('/players/<username>')
def player_details_without_db(username):
    return redirect(url_for('player_details', database='invasion', username=username), code=301)


@app.route('/players/<any({}):database>/<username>'.format(VALID_DATABASES_STRING_LIST))
@app.route('/players/<any({}):database>/<username>/<any(unlockables,evolution,"stats-history",signature):tab>'.format(VALID_DATABASES_STRING_LIST))
def player_details(database, username, tab=None):
    player = rwr.scraper.search_player_by_username(database, username)

    if not player:
        flash(ERROR_PLAYER_NOT_FOUND.format(username=username, database=rwr.utils.get_database_name(database)), 'error')

        return redirect(url_for('players_list', database=database))

    stats = None
    player_evolution_data = None

    if tab is None: # Stats tab (default)
        servers = rwr.scraper.get_servers()

        player.set_playing_on_server(servers)
    elif tab in ['stats-history', 'evolution']:
        if not player.has_stats:
            return redirect(url_for('player_details', database=database, username=username), code=302)

        if tab == 'stats-history':
            g.LAYOUT = 'large'

            per_page = request.args.get('limit', type=int)

            if not per_page or per_page > app.config['LIST_PAGE_SIZES'][-1]:
                per_page = app.config['LIST_PAGE_SIZES'][0]

            stats = player.rwr_account.ordered_stats.paginate(
                page=request.args.get('page', 1, type=int),
                per_page=per_page,
                error_out=False
            )
        elif tab == 'evolution':
            player_evolution_data = RwrAccountStat.get_stats_for_column(player.rwr_account.id)

    return render_template(
        'players/details.html',
        player=player,
        stats=stats,
        player_evolution_data=player_evolution_data
    )


@app.route('/images/players/<username>-<any({}):database>.png'.format(VALID_DATABASES_STRING_LIST))
def dynamic_player_image(username, database):
    return DynamicPlayerImage.create(database, username)


@app.route('/players/<username>/compare')
@app.route('/players/<username>/compare/<username_to_compare_with>')
def players_compare_without_db(username, username_to_compare_with=None):
    if not username_to_compare_with and request.args.get('username_to_compare_with'):
        username_to_compare_with = request.args.get('username_to_compare_with').strip()

    return redirect(url_for('players_compare', database='invasion', username=username, username_to_compare_with=username_to_compare_with), code=301)


@app.route('/players/<any({}):database>/<username>/compare'.format(VALID_DATABASES_STRING_LIST))
@app.route('/players/<any({}):database>/<username>/compare/<username_to_compare_with>'.format(VALID_DATABASES_STRING_LIST))
@app.route('/players/<any({}):database>/<username>/compare/<username_to_compare_with>/<date>'.format(VALID_DATABASES_STRING_LIST))
def players_compare(database, username, username_to_compare_with=None, date=None):
    # Redirect to a SEO-friendly URL if the username_to_compare_with or date query parameters are detected
    if (not username_to_compare_with and request.args.get('username_to_compare_with')) or (not date and request.args.get('date')):
        if not username_to_compare_with:
            username_to_compare_with = request.args.get('username_to_compare_with').strip()

        if not date:
            date = request.args.get('date')

        redirect_params = {
            'database': database,
            'username': username,
            'username_to_compare_with': username_to_compare_with,
            'date': date,
        }

        return redirect(url_for('players_compare', **redirect_params), code=301)

    if not username_to_compare_with:
        abort(404)

    database_name = rwr.utils.get_database_name(database)
    date = arrow.get(date) if date else None

    if date: # Stats history lookup mode
        player_exist = rwr.scraper.search_player_by_username(database, username, check_exist_only=True)

        if not player_exist:
            flash(ERROR_PLAYER_NOT_FOUND.format(username=username, database=database_name), 'error')

            return redirect(url_for('players_list', database=database))

        rwr_account = RwrAccount.get_by_type_and_username(database, username)

        if not rwr_account:
            flash(ERROR_NO_RWR_ACCOUNT.format(username=username, database=database_name, max_players=app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']), 'error')

            return redirect(url_for('player_details', database=database, username=username))

        rwr_account_stat = RwrAccountStat.get_stats_for_date(rwr_account.id, date)

        if not rwr_account_stat:
            flash(ERROR_NO_RWR_ACCOUNT_STATS.format(username=username_to_compare_with, database=database_name, max_players=app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']), 'error')

            return redirect(url_for('player_details', database=database, username=username))

        player = Player.craft(rwr_account, rwr_account_stat)

        player_to_compare_with_exist = rwr.scraper.search_player_by_username(database, username_to_compare_with, check_exist_only=True)

        if not player_to_compare_with_exist:
            flash(ERROR_PLAYER_NOT_FOUND.format(username=username_to_compare_with, database=database_name), 'error')

            return redirect(url_for('player_details', database=database, username=username))

        player_to_compare_with_rwr_account = RwrAccount.get_by_type_and_username(database, username_to_compare_with)

        if not player_to_compare_with_rwr_account:
            flash(ERROR_NO_RWR_ACCOUNT.format(username=username_to_compare_with, database=database_name, max_players=app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']), 'error')

            return redirect(url_for('players_compare', database=database, username=username, username_to_compare_with=username_to_compare_with))

        player_to_compare_with_rwr_account_stat = RwrAccountStat.get_stats_for_date(player_to_compare_with_rwr_account.id, date)

        if not player_to_compare_with_rwr_account_stat:
            flash(ERROR_NO_RWR_ACCOUNT_STATS.format(username=username_to_compare_with, database=database_name, max_players=app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']), 'error')

            return redirect(url_for('players_compare', database=database, username=username, username_to_compare_with=username_to_compare_with))

        player_to_compare_with = Player.craft(player_to_compare_with_rwr_account, player_to_compare_with_rwr_account_stat)
    else: # Live data mode
        player = rwr.scraper.search_player_by_username(database, username)

        if not player:
            flash(ERROR_PLAYER_NOT_FOUND.format(username=username, database=database_name), 'error')

            return redirect(url_for('players_list', database=database))

        player_to_compare_with = rwr.scraper.search_player_by_username(database, username_to_compare_with)

        if not player_to_compare_with:
            flash(ERROR_PLAYER_NOT_FOUND.format(username=username_to_compare_with, database=database_name), 'error')

            return redirect(url_for('player_details', database=database, username=username))

    servers = rwr.scraper.get_servers()

    player.set_playing_on_server(servers)
    player_to_compare_with.set_playing_on_server(servers)

    return render_template(
        'players/compare.html',
        player=player,
        player_to_compare_with=player_to_compare_with,
        date=date
    )


@app.route('/servers')
def servers_list():
    filters = request.args.to_dict()

    if filters:
        servers = rwr.scraper.filter_servers(**filters)
    else:
        servers = rwr.scraper.get_servers()

    locations = rwr.scraper.get_all_servers_locations()
    types = rwr.scraper.get_all_servers_types()
    modes = rwr.scraper.get_all_servers_modes()
    maps = rwr.scraper.get_all_servers_maps()

    if request.args.get('view') == 'extended':
        g.LAYOUT = 'large'

    return render_template(
        'servers/list.html',
        servers=servers,
        locations=locations,
        types=types,
        modes=modes,
        maps=maps
    )


@app.route('/servers/<ip>:<int:port>')
@app.route('/servers/<ip>:<int:port>/<slug>')
def server_details(ip, port, slug=None):
    server = rwr.scraper.get_server_by_ip_and_port(ip, port)

    if not server:
        flash('Sorry, this server wasn\'t found.', 'error')

        return redirect(url_for('servers_list'))

    if not slug:
        return redirect(server.link, code=301)

    server_players_data = ServerPlayerCount.server_players_data(ip, port) if server.is_dedicated else None

    return render_template(
        'servers/details.html',
        server_players_data=server_players_data,
        server=server
    )


@app.route('/servers/<ip>:<int:port>/banner')
@app.route('/servers/<ip>:<int:port>/<slug>/banner')
def server_banner(ip, port, slug=None):
    server = rwr.scraper.get_server_by_ip_and_port(ip, port)

    if not server:
        flash('Sorry, this server wasn\'t found.', 'error')

        return redirect(url_for('servers_list'))

    if not slug:
        return redirect(url_for('server_banner', ip=server.ip, port=server.port, slug=server.name_slug), code=301)

    if not server.is_dedicated:
        flash('Server banner is only available for dedicated servers.', 'error')

        return redirect(server.link, code=302)

    return render_template(
        'servers/banner.html',
        server=server
    )


@app.route('/images/servers/<ip>-<int:port>.png')
def dynamic_server_image(ip, port):
    return DynamicServerImage.create(ip, port)
