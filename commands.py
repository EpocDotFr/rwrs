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
    from models import RwrRootServer, RwrRootServerStatus
    from rwrs import db
    import rwr.constants
    import helpers

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
        'total_players_peak_count': {'date_var_name': 'total_players_peak_date', 'current': current_total_players_count},
        'online_players_peak_count': {'date_var_name': 'online_players_peak_date', 'current': current_online_players_count},
        'online_servers_peak_count': {'date_var_name': 'online_servers_peak_date', 'current': current_online_servers_count},
        'active_servers_peak_count': {'date_var_name': 'active_servers_peak_date', 'current': current_active_servers_count}
    }

    peak_values = Variable.get_many_values(peak_refs.keys())
    vars_to_update = {}

    for name in peak_refs.keys():
        click.echo('  ' + name)

        if name not in peak_values:
            peak_values[name] = 0

        if peak_refs[name]['current'] > peak_values[name]:
            vars_to_update[name] = peak_refs[name]['current']
            vars_to_update[peak_refs[name]['date_var_name']] = arrow.utcnow().floor('minute')

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
    """Runs the RWRS Discord bot."""
    from discord.bot import RwrsBot

    click.echo('Initializing bot')

    rwrs_discord_bot = RwrsBot()

    click.echo('Running bot')

    rwrs_discord_bot.run()
