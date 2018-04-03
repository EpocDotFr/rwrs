from rwrs import app
import rwr.constants
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
    from rwrs import db
    import helpers
    import arrow

    click.echo('Pinging servers')

    hosts_to_ping = [server['host'] for group in rwr.constants.ROOT_RWR_SERVERS for server in group['servers']]

    for host in hosts_to_ping:
        click.echo(host, nl=False)

        is_server_up = helpers.ping(host)

        if is_server_up:
            click.secho(' Up', fg='green')
        else:
            click.secho(' Down', fg='red')

        rwr_root_server = RwrRootServer.query.filter(RwrRootServer.host == host).first()

        if not rwr_root_server:
            rwr_root_server = RwrRootServer()
            rwr_root_server.host = host

        rwr_root_server.status = RwrRootServerStatus.UP if is_server_up else RwrRootServer.DOWN

        db.session.add(rwr_root_server)

    Variable.set_value('last_root_rwr_servers_check', arrow.utcnow().floor('minute'))

    click.echo('Persisting to database')

    db.session.commit()

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
@click.option('--database', '-d', help='Stats database to pull data from', type=click.Choice(rwr.constants.VALID_DATABASES), default='invasion')
def save_players_stats(database):
    """Get and persist the players stats."""
    from models import RwrAccount, RwrAccountType, RwrAccountStat
    from rwrs import db
    import rwr.scraper

    scraper = rwr.scraper.DataScraper()

    sort = rwr.constants.PlayersSort.SCORE
    max_players = 1000
    chunks_size = 200
    rwr_account_type = RwrAccountType(database.upper())

    click.echo('Getting the first {} {} players stats, ordered by {}, chunk size {}'.format(
        max_players,
        database,
        sort,
        chunks_size
    ))

    for start in range(0, max_players, chunks_size):
        click.echo('  Chunk start: {}'.format(start))

        players = scraper.get_players(database, sort=sort, start=start, limit=chunks_size)

        if not players:
            click.echo('No more players to handle')

            continue

        click.echo('Getting existing RWR accounts')

        all_player_names = [player.username for player in players]

        existing_rwr_accounts = RwrAccount.query.filter(
            RwrAccount.username.in_(all_player_names),
            RwrAccount.type == rwr_account_type
        ).all()

        existing_rwr_accounts_by_username = {rwr_account.username: rwr_account for rwr_account in existing_rwr_accounts}

        for player in players:
            if player.username not in existing_rwr_accounts_by_username:
                rwr_account = RwrAccount()

                rwr_account.username = player.username
                rwr_account.type = rwr_account_type

                db.session.add(rwr_account)
            else:
                rwr_account = existing_rwr_accounts_by_username[player.username]

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
            rwr_account_stat.rwr_account = rwr_account

            db.session.add(rwr_account_stat)

        click.echo('Persisting to database')

        db.session.commit()

    click.secho('Done', fg='green')
