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
    """Check the status of the RWR root servers."""
    from models import RwrRootServer, RwrRootServerStatus, Variable
    from disco.api.client import APIClient as DiscordAPIClient
    from flask import url_for
    from rwrs import db
    import rwr.constants
    import helpers
    import arrow

    click.echo('Pinging servers')

    hosts_to_ping = [server['host'] for group in rwr.constants.ROOT_RWR_SERVERS for server in group['servers']]
    rwr_root_servers = RwrRootServer.query.filter(RwrRootServer.host.in_(hosts_to_ping)).all()
    rwr_root_servers_by_host = {rwr_root_server.host: rwr_root_server for rwr_root_server in rwr_root_servers}
    servers_down_count_then = sum([1 for rwr_root_server in rwr_root_servers if rwr_root_server.status == RwrRootServerStatus.DOWN])
    servers_down_count_now = 0

    for host in hosts_to_ping:
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
            message = ':warning: Online multiplayer is having issues right now. Are the devs aware? If not, poke **pasik** or **JackMayol**. Some details here: {}'.format(url_for('online_multiplayer_status', _external=True))
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
    import steam_api
    import arrow

    scraper = rwr.scraper.DataScraper()

    click.echo('Clearing cache')

    cache.delete_memoized(rwr.scraper.DataScraper.get_servers)
    cache.delete_memoized(ServerPlayerCount.server_players_data)
    cache.delete_memoized(ServerPlayerCount.servers_data)
    cache.delete_memoized(steam_api.Client.get_current_players_count_for_app)
    cache.delete_memoized(SteamPlayerCount.players_data)

    click.echo('Getting current players on Steam')

    steam_api_client = steam_api.Client(app.config['STEAM_API_KEY'])

    steam_player_count = SteamPlayerCount()
    steam_player_count.count = steam_api_client.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])

    current_total_players_count = steam_player_count.count

    db.session.add(steam_player_count)

    click.echo('Getting current players on servers')

    servers = scraper.get_servers()

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
def save_players_stats():
    """Get and persist the players stats."""
    from models import RwrAccount, RwrAccountType, RwrAccountStat
    from rwrs import db
    import rwr.scraper
    import arrow

    players_sort = rwr.constants.PlayersSort.XP
    chunks = 100
    players_count = app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']

    scraper = rwr.scraper.DataScraper()

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

            players = scraper.get_players(database, sort=players_sort, start=start, limit=chunks, basic=True)

            if not players:
                click.secho('No more players to handle', fg='green')

                break

            click.echo('  Getting existing RWR accounts')

            all_player_names = [player.username for player in players]

            existing_rwr_accounts = RwrAccount.query.filter(
                RwrAccount.type == rwr_account_type,
                RwrAccount.username.in_(all_player_names)
            ).all()

            rwr_accounts_by_username = {rwr_account.username: rwr_account for rwr_account in existing_rwr_accounts}

            click.echo('  Creating unexisting RWR accounts')

            for player in players:
                click.echo('    ' + player.username)

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

            click.echo('  Saving stats')

            for player in players:
                click.echo('    ' + player.username)

                rwr_account_stat = RwrAccountStat()

                rwr_account_stat.leaderboard_position = player.position
                rwr_account_stat.xp = player.xp
                rwr_account_stat.score = player.score
                rwr_account_stat.kills = player.kills
                rwr_account_stat.deaths = player.deaths
                rwr_account_stat.kd_ratio = player.kd_ratio
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

                db.session.add(rwr_account_stat)

            db.session.commit()

    click.secho('Done', fg='green')
