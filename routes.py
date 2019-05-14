from models import SteamPlayerCount, ServerPlayerCount, Variable, RwrAccountStat, RwrAccount
from flask import render_template, abort, request, redirect, url_for, flash, g, jsonify
from flask_login import login_required, current_user, logout_user
from dynamic_image import DynamicServerImage, DynamicPlayerImage
from rwr.player import Player
from rwrs import app, oid, db
from models import User
import rwr.constants
import flask_openid
import rwr.scraper
import rwr.utils
import arrow
import forms
import uuid


ERROR_PLAYER_NOT_FOUND = 'Sorry, the player "{username}" wasn\'t found in the {database} players list. Maybe this player hasn\'t already played on a ranked server yet. If this player started to play today on a ranked server, please wait until tomorrow as stats are refreshed daily.'
ERROR_NO_RWR_ACCOUNT = 'Sorry, stats history isn\'t recorded for {username}. He/she must be part of the {database} {max_players} most experienced players.'
ERROR_NO_RWR_ACCOUNT_STATS = 'No stats were found for the given date for {username}. Are you sure he/she is/was part of the {database} {max_players} most experienced players?'


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


@app.route('/sign-in')
@oid.loginhandler
def sign_in():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.args.get('go_to_steam'):
        return oid.try_login(flask_openid.COMMON_PROVIDERS['steam'])

    return render_template(
        'users/sign_in.html',
        oid_error_message=oid.fetch_error()
    )


@app.route('/sign-out')
@login_required
def sign_out():
    logout_user()

    flash('You are now signed out, see ya!', 'success')

    return redirect(url_for('home'))


@app.route('/users/<int:user_id>/<slug>')
def user_profile(user_id, slug):
    user = User.query.get(user_id)

    if not user:
        abort(404)

    if not user.is_profile_public and ((current_user.is_authenticated and user.id != current_user.id) or not current_user.is_authenticated):
        abort(404)

    return render_template(
        'users/profile.html',
        user=user
    )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    form = forms.UserGeneralSettingsForm(obj=current_user)

    if form.validate_on_submit():
        form.populate_user(current_user)

        db.session.add(current_user)
        db.session.commit()

        flash('Settings saved successfully.', 'success')

        return redirect(url_for('user_settings'))

    return render_template(
        'users/settings.html',
        form=form
    )


@app.route('/settings/regenerate-pat', methods=['POST'])
@login_required
def regenerate_pat():
    status = 200

    if not request.is_xhr:
        status = 400
        result = {'status': 'failure', 'data': {'message': 'Invalid request.'}}
    else:
        try:
            current_user.pat = uuid.uuid4()

            db.session.add(current_user)
            db.session.commit()

            result = {'status': 'success', 'data': {'new_pat': str(current_user.pat)}}
        except Exception as e:
            status = 500
            result = {'status': 'failure', 'data': {'message': str(e)}}

    return jsonify(result), status


@app.route('/my-friends', methods=['GET', 'POST'])
def my_friends():
    form = None

    if current_user.is_authenticated:
        form = forms.UserFriendForm()

        if form.validate_on_submit():
            current_user.add_friend(form.username.data.upper())

            db.session.commit()

            flash('You have a new friend!', 'success')

            return redirect(url_for('my_friends'))

    return render_template(
        'users/friends.html',
        form=form
    ), 200 if current_user.is_authenticated else 401


@app.route('/my-friends/add/<username>')
@login_required
def add_friend(username):
    form = forms.UserFriendForm(data={'username': username}, meta={'csrf': False})

    if form.validate():
        current_user.add_friend(form.username.data.upper())

        db.session.commit()

        flash('You have a new friend!', 'success')
    else:
        flash('Invalid request.', 'error')

    return redirect(request.referrer) # TODO Redirect to correct URL


@app.route('/my-friends/remove/<username>')
@login_required
def remove_friend(username):
    if current_user.remove_friend(username):
        db.session.commit()

        flash('Friend removed. Sad.', 'success')
    else:
        flash('Friend not found.', 'error')

    return redirect(request.referrer) # TODO Redirect to correct URL


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
    return redirect(app.config['STATUS_PAGE_URL'], code=301)


@app.route('/api')
def api_home():
    return redirect(url_for('static', filename='/api_doc.html'), code=301)


@app.route('/players')
def players_list_without_db():
    database = request.args.get('database', 'invasion')
    username = request.args.get('username')

    if username:
        username = username.strip().upper()

        # Redirect to a SEO-friendly URL if the username query parameter is detected
        return redirect(url_for('player_details', database=database, username=username), code=301)

    return redirect(url_for('players_list', database=database), code=301)


@app.route('/claim', methods=['GET', 'POST'])
@login_required
def player_claim():
    # Player claim form may be pre-filled with values in query string parameters
    form_default_values = {
        'type': request.args.get('type'),
        'username': request.args.get('username')
    }

    form = forms.PlayerClaimForm(data=form_default_values)

    if form.validate_on_submit():
        rwr_account = RwrAccount.get_by_type_and_username(
            form.type.data,
            form.username.data.upper(),
            create_if_unexisting=True
        )

        rwr_account.init_claim(current_user.id)

        db.session.add(rwr_account)
        db.session.commit()

        return redirect(url_for('player_finalize_claim', rwr_account_id=rwr_account.id))

    return render_template(
        'players/claim.html',
        form=form
    )


@app.route('/claim/<int:rwr_account_id>', methods=['GET', 'POST'])
@login_required
def player_finalize_claim(rwr_account_id):
    rwr_account = RwrAccount.query.get(rwr_account_id)
    error_message = None

    if not rwr_account or rwr_account.claim_initiated_by_user_id != current_user.id:
        abort(404)

    database = rwr_account.type.value.lower()
    username = rwr_account.username

    if rwr_account.has_claim_expired():
        db.session.add(rwr_account)
        db.session.commit()

        flash('Sorry, you didn\'t finalized the claim procedure in time. Please try again.', 'error')

        return redirect(url_for('player_claim', type=database, username=username))

    if request.method == 'POST':
        if rwr.scraper.filter_servers(database=database, username=username):
            rwr_account.claim(current_user.id)

            db.session.add(rwr_account)
            db.session.commit()

            flash('Awesome, you successfully claimed this RWR account!', 'success')

            return redirect(rwr_account.link)
        else:
            error_message = '<strong>{}</strong> wasn\'t found connected on any ranked (official) <strong>{}</strong> server. Please wait a few seconds and try again.'.format(username, rwr_account.type_display)

    return render_template(
        'players/finalize_claim.html',
        error_message=error_message,
        rwr_account=rwr_account,
        milliseconds_remaining=rwr_account.claim_possible_until.timestamp * 1000
    )


@app.route('/players/<any({}):database>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
def players_list(database):
    args = request.args.to_dict()

    args['sort'] = args.get('sort', rwr.constants.PlayersSort.SCORE.value)

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


@app.route('/players/<any({}):database>/<username>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
@app.route('/players/<any({}):database>/<username>/<any(evolution,"stats-history",signature):tab>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
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
            player_evolution_data = RwrAccountStat.get_stats_for_column(player.rwr_account)

    return render_template(
        'players/details.html',
        player=player,
        stats=stats,
        player_evolution_data=player_evolution_data
    )


@app.route('/images/players/<username>-<any({}):database>.png'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
def dynamic_player_image(username, database):
    return DynamicPlayerImage.create(database, username)


@app.route('/popover/players/<any({}):database>/<username>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
def player_popover(database, username):
    player = rwr.scraper.search_player_by_username(database, username)

    return render_template(
        'players/popover.html',
        player=player
    )


@app.route('/players/<username>/compare')
@app.route('/players/<username>/compare/<username_to_compare_with>')
def players_compare_without_db(username, username_to_compare_with=None):
    if not username_to_compare_with and request.args.get('username_to_compare_with'):
        username_to_compare_with = request.args.get('username_to_compare_with').strip()

    return redirect(url_for('players_compare', database='invasion', username=username, username_to_compare_with=username_to_compare_with), code=301)


@app.route('/players/<any({}):database>/<username>/compare'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
@app.route('/players/<any({}):database>/<username>/compare/<username_to_compare_with>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
@app.route('/players/<any({}):database>/<username>/compare/<username_to_compare_with>/<date>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
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
