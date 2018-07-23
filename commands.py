from rwrs import app
import click


@app.cli.command()
def cc():
    """Clear the cache."""
    from rwrs import cache

    click.echo('Clearing cache')

    cache.clear()

    click.secho('Done', fg='green')


@app.cli.command()
def get_root_rwr_servers_status():
    """Check the status of the root RWR servers."""
    from models import RwrRootServer, RwrRootServerStatus, Variable
    from disco.api.client import APIClient as DiscordAPIClient
    from flask import url_for
    from rwrs import db
    import rwr.constants
    import helpers
    import arrow

    click.echo('Pinging servers')

    rwr_root_servers = RwrRootServer.query.filter(RwrRootServer.host.in_(rwr.constants.ROOT_RWR_HOSTS)).all()
    rwr_root_servers_by_host = {rwr_root_server.host: rwr_root_server for rwr_root_server in rwr_root_servers}
    servers_down_count_then = sum([1 for rwr_root_server in rwr_root_servers if rwr_root_server.status == RwrRootServerStatus.DOWN])
    servers_down_count_now = 0

    for host in rwr.constants.ROOT_RWR_HOSTS:
        click.echo(host, nl=False)

        is_server_up = helpers.ping(host)

        if is_server_up:
            click.secho(' Up', fg='green')
        else:
            click.secho(' Down', fg='red')

            servers_down_count_now += 1

        if host not in rwr_root_servers_by_host:
            rwr_root_server = RwrRootServer()
            rwr_root_server.host = host
        else:
            rwr_root_server = rwr_root_servers_by_host[host]

        rwr_root_server.status = RwrRootServerStatus.UP if is_server_up else RwrRootServerStatus.DOWN

        db.session.add(rwr_root_server)

    Variable.set_value('last_root_rwr_servers_check', arrow.utcnow().floor('minute'))

    click.echo('Persisting to database')

    db.session.commit()

    message = None

    if servers_down_count_then == 0 and servers_down_count_now > 0:
        with app.app_context():
            message = ':warning: Online multiplayer is having issues right now. Some details here: {}'.format(url_for('online_multiplayer_status', _external=True))
    elif servers_down_count_then > 0 and servers_down_count_now == 0:
        message = ':white_check_mark: Outage update: online multiplayer is back up and running!'

    if message:
        click.echo('Sending Discord bot message')

        discord_api_client = DiscordAPIClient(app.config['DISCORD_BOT_TOKEN'])
        discord_api_client.channels_messages_create(app.config['DISCORD_BOT_CHANNEL_ID'], message)

    click.secho('Done', fg='green')


@app.cli.command()
def get_players_count():
    """Store the number of players."""
    from models import ServerPlayerCount, SteamPlayerCount, Variable
    from rwrs import cache, db
    import rwr.scraper
    import steam
    import arrow

    click.echo('Clearing cache')

    cache.delete_memoized(rwr.scraper.get_servers)
    cache.delete_memoized(ServerPlayerCount.server_players_data)
    cache.delete_memoized(ServerPlayerCount.servers_data)
    cache.delete_memoized(steam.SteamworksApiClient.get_current_players_count_for_app)
    cache.delete_memoized(SteamPlayerCount.players_data)

    click.echo('Getting current players on Steam')

    steamworks_api_client = steam.SteamworksApiClient(app.config['STEAM_API_KEY'])

    steam_player_count = SteamPlayerCount()
    steam_player_count.count = steamworks_api_client.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])

    current_total_players_count = steam_player_count.count

    db.session.add(steam_player_count)

    click.echo('Getting current players on servers')

    servers = rwr.scraper.get_servers()

    current_online_players_count = 0
    current_online_servers_count = 0
    current_active_servers_count = 0

    for server in servers:
        click.echo('  {} ({}, {})'.format(server.name, server.players.current, server.ip_and_port))

        server_player_count = ServerPlayerCount()
        server_player_count.ip = server.ip
        server_player_count.port = server.port
        server_player_count.count = server.players.current

        current_online_players_count += server.players.current
        current_online_servers_count += 1

        if server.players.current > 0:
            current_active_servers_count += 1

        db.session.add(server_player_count)

    click.echo('Getting peaks')

    peak_refs = {
        'total_players_peak': current_total_players_count,
        'online_players_peak': current_online_players_count,
        'online_servers_peak': current_online_servers_count,
        'active_servers_peak': current_active_servers_count
    }

    peak_values = Variable.get_many_values([name + '_count' for name in peak_refs.keys()])
    vars_to_update = {}

    for name in peak_refs.keys():
        click.echo('  ' + name)

        name_count = name + '_count'
        name_date = name + '_date'

        peak_value = peak_values[name_count] if name_count in peak_values else 0

        if peak_refs[name] >= peak_value:
            vars_to_update[name_count] = peak_refs[name]
            vars_to_update[name_date] = arrow.utcnow().floor('minute')

    Variable.set_many_values(vars_to_update)

    click.echo('Persisting to database')

    db.session.commit()

    click.secho('Done', fg='green')


@app.cli.command()
def clean_players_count():
    """Delete old players count."""
    from models import ServerPlayerCount, SteamPlayerCount
    from rwrs import db

    click.echo('Deleting old data')

    old_entries = ServerPlayerCount.query.get_old_entries()
    old_entries.extend(SteamPlayerCount.query.get_old_entries())

    for old_entry in old_entries:
        db.session.delete(old_entry)

    click.echo('Persisting to database')

    db.session.commit()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--steamdir', '-g', help='Steam root directory')
def extract_ranks(steamdir):
    """Extract ranks data and images from RWR."""
    import rwr.extractors

    context = click.get_current_context()

    if not steamdir:
        click.echo(extract_ranks.get_help(context))
        context.exit()

    click.echo('Extraction started')

    extractor = rwr.extractors.RanksExtractor(steamdir)
    extractor.extract()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--steamdir', '-g', help='Steam root directory')
def extract_unlockables(steamdir):
    """Extract unlockables data and images from RWR."""
    import rwr.extractors

    context = click.get_current_context()

    if not steamdir:
        click.echo(extract_unlockables.get_help(context))
        context.exit()

    click.echo('Extraction started')

    extractor = rwr.extractors.UnlockablesExtractor(steamdir)
    extractor.extract()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--steamdir', '-g', help='Steam root directory')
def extract_maps_data(steamdir):
    """Extract maps data from RWR."""
    import rwr.extractors

    context = click.get_current_context()

    if not steamdir:
        click.echo(extract_maps_data.get_help(context))
        context.exit()

    click.echo('Extraction started')

    extractor = rwr.extractors.MapsDataExtractor(steamdir)
    extractor.extract()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--steamdir', '-g', help='Steam root directory')
def extract_minimaps(steamdir):
    """Extract minimaps from RWR."""
    import rwr.extractors

    context = click.get_current_context()

    if not steamdir:
        click.echo(extract_minimaps.get_help(context))
        context.exit()

    click.echo('Extraction started')

    extractor = rwr.extractors.MinimapsImageExtractor(steamdir)
    extractor.extract()

    click.secho('Done', fg='green')


@app.cli.command()
def run_discord_bot():
    """Run the RWRS Discord bot."""
    from discord.bot import RwrsBot

    click.echo('Initializing bot')

    rwrs_discord_bot = RwrsBot()

    click.echo('Running bot')

    rwrs_discord_bot.run()


@app.cli.command()
@click.option('--reset', is_flag=True, help='Reset all RWR accounts and stats')
def save_players_stats(reset):
    """Get and persist the players stats."""
    from models import RwrAccount, RwrAccountType, RwrAccountStat
    from rwrs import db, cache
    import rwr.scraper
    import arrow

    if reset and click.confirm('Are you sure to reset all RWR accounts and stats?'):
        RwrAccountStat.query.delete()
        RwrAccount.query.delete()
        db.session.commit()

    players_sort = rwr.constants.PlayersSort.XP
    players_count = app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']
    chunks = 100

    cache.delete_memoized(rwr.scraper.get_players)

    for database in rwr.constants.VALID_DATABASES:
        rwr_account_type = RwrAccountType(database.upper())

        click.echo('Saving the first {} {} players stats (ordered by {}, chunk size {})'.format(
            players_count,
            database,
            players_sort,
            chunks
        ))

        for start in range(0, players_count, chunks):
            click.echo('  Chunk start: {}'.format(start))

            players = rwr.scraper.get_players(database, sort=players_sort, start=start, limit=chunks)

            if not players:
                click.secho('No more players to handle', fg='green')

                break

            all_player_names = [player.username for player in players]

            existing_rwr_accounts = RwrAccount.query.filter(
                RwrAccount.type == rwr_account_type,
                RwrAccount.username.in_(all_player_names)
            ).all()

            rwr_accounts_by_username = {rwr_account.username: rwr_account for rwr_account in existing_rwr_accounts}

            # Create RWR accounts if they do not exists / touch the updated_at timestamp if they exists
            for player in players:
                if player.username not in rwr_accounts_by_username:
                    rwr_account = RwrAccount()

                    rwr_account.username = player.username
                    rwr_account.type = rwr_account_type

                    rwr_accounts_by_username[player.username] = rwr_account
                else:
                    rwr_account = rwr_accounts_by_username[player.username]

                    rwr_account.updated_at = arrow.utcnow().floor('minute')

                db.session.add(rwr_account)

            db.session.commit()

            # Create all the RwrAccountStat objects for each players
            all_rwr_accounts_stat = []

            for player in players:
                rwr_account_stat = RwrAccountStat()

                rwr_account_stat.leaderboard_position = player.leaderboard_position
                rwr_account_stat.xp = player.xp
                rwr_account_stat.kills = player.kills
                rwr_account_stat.deaths = player.deaths
                rwr_account_stat.time_played = player.time_played
                rwr_account_stat.longest_kill_streak = player.longest_kill_streak
                rwr_account_stat.targets_destroyed = player.targets_destroyed
                rwr_account_stat.vehicles_destroyed = player.vehicles_destroyed
                rwr_account_stat.soldiers_healed = player.soldiers_healed
                rwr_account_stat.teamkills = player.teamkills
                rwr_account_stat.distance_moved = player.distance_moved
                rwr_account_stat.shots_fired = player.shots_fired
                rwr_account_stat.throwables_thrown = player.throwables_thrown
                rwr_account_stat.rwr_account_id = rwr_accounts_by_username[player.username].id

                rwr_account_stat.compute_hash()

                # Get the latest RwrAccountStat object saved for this RwrAccount and check if its data is not the same
                already_existing_rwr_account_stat = RwrAccountStat.query.filter(
                    RwrAccountStat.rwr_account_id == rwr_account_stat.rwr_account_id
                ).order_by(RwrAccountStat.created_at.desc()).first()

                if not already_existing_rwr_account_stat or already_existing_rwr_account_stat.hash != rwr_account_stat.hash:
                    all_rwr_accounts_stat.append(rwr_account_stat)

            # Finally save stats for all eligible players
            db.session.add_all(all_rwr_accounts_stat)
            db.session.commit()

    click.secho('Done', fg='green')


@app.cli.command()
def save_ranked_servers_admins():
    """Retrieve and save the ranked servers admins."""
    from lxml import etree
    import requests
    import helpers

    click.echo('Retrieving admins list')

    try:
        response = requests.get('http://rwr.runningwithrifles.com/shared/admins.xml')

        response.raise_for_status()

        admins_xml = etree.fromstring(response.text)
    except Exception as e:
        click.secho(str(e), fg='red')

        return

    admins = [item.get('value') for item in admins_xml.iterchildren('item')]

    click.echo('Saving to {}'.format(app.config['RANKED_SERVERS_ADMINS_FILE']))

    helpers.save_json(app.config['RANKED_SERVERS_ADMINS_FILE'], admins)

    click.secho('Done', fg='green')


@app.cli.command()
def migrate_to_percona():
    from models import ServerPlayerCount, SteamPlayerCount, Variable, VariableType, RwrRootServer, RwrRootServerStatus, RwrAccount, RwrAccountType, RwrAccountStat
    from rwrs import db
    import sqlite3
    import socket
    import struct

    def long2ip(long):
        """Convert an integer IP to its string representation."""
        return socket.inet_ntoa(struct.pack('!L', long))

    def db_chunks(sqlite_db, table):
        offset = 0
        limit = 100

        while True:
            rows = sqlite_db.execute('SELECT * FROM {table} LIMIT {offset}, {limit}'.format(table=table, offset=offset, limit=limit)).fetchall()

            if not rows:
                break

            yield rows

            offset += limit

    # -----------------------------------------------------------------------
    # servers_player_count.sqlite

    sqlite_db = sqlite3.connect('storage/data/servers_player_count.sqlite')
    sqlite_db.row_factory = sqlite3.Row

    rows = sqlite_db.execute('SELECT * FROM servers_player_count').fetchall()
    new_rows = []

    for row in rows:
        model = ServerPlayerCount()
        model.id = row['id']
        model.measured_at = row['measured_at']
        model.count = row['count']
        model.ip = long2ip(row['ip'])
        model.port = row['port']

        new_rows.append(model)

    db.session.add_all(new_rows)
    db.session.commit()

    sqlite_db.close()

    # -----------------------------------------------------------------------
    # steam_players_count.sqlite

    sqlite_db = sqlite3.connect('storage/data/steam_players_count.sqlite')
    sqlite_db.row_factory = sqlite3.Row

    rows = sqlite_db.execute('SELECT * FROM steam_players_count').fetchall()
    new_rows = []

    for row in rows:
        model = SteamPlayerCount()
        model.id = row['id']
        model.measured_at = row['measured_at']
        model.count = row['count']

        new_rows.append(model)

    db.session.add_all(new_rows)
    db.session.commit()

    sqlite_db.close()

    # -----------------------------------------------------------------------
    # db.sqlite

    sqlite_db = sqlite3.connect('storage/data/db.sqlite')
    sqlite_db.row_factory = sqlite3.Row

    # variables

    rows = sqlite_db.execute('SELECT * FROM variables').fetchall()
    new_rows = []

    for row in rows:
        model = Variable()
        model.id = row['id']
        model.name = row['name']
        model.value = row['value']
        model.type = VariableType(row['type'])

        new_rows.append(model)

    db.session.add_all(new_rows)
    db.session.commit()

    # rwr_root_servers

    rows = sqlite_db.execute('SELECT * FROM rwr_root_servers').fetchall()
    new_rows = []

    for row in rows:
        model = RwrRootServer()
        model.id = row['id']
        model.host = row['host']
        model.status = RwrRootServerStatus(row['status'])

        new_rows.append(model)

    db.session.add_all(new_rows)
    db.session.commit()

    # rwr_accounts

    for rows in db_chunks(sqlite_db, 'rwr_accounts'):
        new_rows = []

        for row in rows:
            model = RwrAccount()
            model.id = row['id']
            model.type = RwrAccountType(row['type'])
            model.username = row['username']
            model.created_at = row['created_at']
            model.updated_at = row['updated_at']

            new_rows.append(model)

        db.session.add_all(new_rows)
        db.session.commit()

    sqlite_db.close()

    # -----------------------------------------------------------------------
    # rwr_account_stats.sqlite

    sqlite_db = sqlite3.connect('storage/data/rwr_account_stats.sqlite')
    sqlite_db.row_factory = sqlite3.Row

    for rows in db_chunks(sqlite_db, 'rwr_account_stats'):
        new_rows = []

        for row in rows:
            model = RwrAccountStat()
            model.id = row['id']
            model.leaderboard_position = row['leaderboard_position']
            model.xp = row['xp']
            model.kills = row['kills']
            model.deaths = row['deaths']
            model.time_played = row['time_played']
            model.longest_kill_streak = row['longest_kill_streak']
            model.targets_destroyed = row['targets_destroyed']
            model.vehicles_destroyed = row['vehicles_destroyed']
            model.soldiers_healed = row['soldiers_healed']
            model.teamkills = row['teamkills']
            model.distance_moved = row['distance_moved']
            model.shots_fired = row['shots_fired']
            model.throwables_thrown = row['throwables_thrown']
            model.hash = row['hash']
            model.created_at = row['created_at']
            model.rwr_account_id = row['rwr_account_id']

            new_rows.append(model)

        db.session.add_all(new_rows)
        db.session.commit()

    sqlite_db.close()
