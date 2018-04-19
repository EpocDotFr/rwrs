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
def generate_maps_tiles():
    """Generate the maps tiles for the gallery."""
    from PIL import Image
    import rwr.utils
    import os

    tile_size = app.config['MAPS_GALLERY_TILE_SIZE']
    min_zoom = app.config['MAPS_GALLERY_MIN_ZOOM']
    max_zoom = app.config['MAPS_GALLERY_MAX_ZOOM']

    maps = rwr.utils.get_maps(has_minimap=True)

    for map in maps:
        minimap_path = os.path.join(app.config['MINIMAPS_IMAGES_DIR'], map['server_type'], map['id'] + '.png')

        click.echo(minimap_path)

        original_minimap_image = Image.open(minimap_path)

        for zoom_level in range(min_zoom, max_zoom + 1):
            num_tiles = 2 ** zoom_level
            map_size = num_tiles * tile_size

            click.echo('Zoom level {zoom_level} (edges: {num_tiles} tiles, {pixels} pixels)'.format(
                zoom_level=zoom_level,
                num_tiles=num_tiles,
                pixels=map_size
            ))

            working_map_image = original_minimap_image.resize((map_size, map_size), Image.LANCZOS)

            for x in range(0, num_tiles):
                for y in range(0, num_tiles):
                    tile_image = working_map_image.crop((
                        x * tile_size,
                        y * tile_size,
                        (x * tile_size) + tile_size,
                        (y * tile_size) + tile_size
                    ))

                    tile_path = os.path.join(app.config['MAPS_TILES_DIR'], map['server_type'], map['id'], str(zoom_level), str(x), '{}.png'.format(y))

                    tile_dir = os.path.dirname(tile_path)

                    if not os.path.isdir(tile_dir):
                        os.makedirs(tile_dir)

                    tile_image.save(tile_path, optimize=True)

    click.secho('Done', fg='green')
