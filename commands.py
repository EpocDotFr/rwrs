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
@click.option('--reset', is_flag=True, help='Reset all RWR accounts and stats')
def save_players_stats(reset):
    """Get and persist the players stats."""
    from models import RwrAccount, RwrAccountType, RwrAccountStat
    from rwrs import db
    import rwr.scraper
    import arrow

    if reset and click.confirm('Are you sure to reset all RWR accounts and stats?'):
        RwrAccountStat.query.delete()
        RwrAccount.query.delete()
        db.session.commit()

    players_sort = rwr.constants.PlayersSort.XP
    players_count = app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']
    now = arrow.utcnow().floor('day')
    chunks = 100

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

            all_player_names = [player.username for player in players]

            existing_rwr_accounts = RwrAccount.query.filter(
                RwrAccount.type == rwr_account_type,
                RwrAccount.username.in_(all_player_names)
            ).all()

            rwr_accounts_by_username = {rwr_account.username: rwr_account for rwr_account in existing_rwr_accounts}

            # Remove players already having an RWR account and that are already up-to-date in the DB to prevent saving duplicate stats
            for player in players:
                if player.username in rwr_accounts_by_username and rwr_accounts_by_username[player.username].updated_at.floor('day') >= now:
                    players.remove(player)

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

                rwr_account_stat.leaderboard_position = player.position
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

                all_rwr_accounts_stat.append(rwr_account_stat)

            # Remove all RwrAccountStat objects already existing in the DB (to prevent duplicates when stats didn't changed)
            all_rwr_accounts_stat_hashes = [rwr_account_stat.hash for rwr_account_stat in all_rwr_accounts_stat]

            already_existing_rwr_accounts_stats = RwrAccountStat.query.filter(
                RwrAccountStat.hash.in_(all_rwr_accounts_stat_hashes)
            ).all()

            for already_existing_rwr_account_stats in already_existing_rwr_accounts_stats:
                for rwr_account_stat in all_rwr_accounts_stat:
                    if already_existing_rwr_account_stats.hash == rwr_account_stat.hash:
                        all_rwr_accounts_stat.remove(rwr_account_stat)

            # Finally save stats for eligible  players
            db.session.add_all(all_rwr_accounts_stat)
            db.session.commit()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--directory', '-d', help='Directory containing the rwrtrack CSV files')
@click.option('--reset', is_flag=True, help='Reset all RWR accounts and stats')
def import_rwrtrack_data(directory, reset):
    """Import data from rwrtrack."""
    from models import RwrAccount, RwrAccountType, RwrAccountStat
    from glob import glob
    from rwrs import db
    import helpers
    import arrow
    import csv
    import os

    if reset and click.confirm('Are you sure to reset all RWR accounts and stats?'):
        RwrAccountStat.query.delete()
        RwrAccount.query.delete()
        db.session.commit()

    csv_filenames = glob(os.path.join(directory, '*.csv'))
    now = arrow.utcnow().floor('day')
    chunks = 100

    click.echo('{} files to import'.format(len(csv_filenames)))

    for csv_filename in csv_filenames:
        click.echo('Opening ' + csv_filename)

        created_at = arrow.get(os.path.splitext(os.path.basename(csv_filename))[0]).floor('day')

        with open(csv_filename, 'r', encoding='utf-8', newline='') as f:
            next(f, None) # Ignore first line as it's the CSV header

            csv_data = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC)
            leaderboard_position = 1
            start = 0

            for players in helpers.chunks(list(csv_data), chunks):
                click.echo('  Chunk start: {}'.format(start))

                all_player_names = [player[0] for player in players] # FIXME Username isn't properly encoded, try to decode it to unicode

                existing_rwr_accounts = RwrAccount.query.filter(
                    RwrAccount.type == RwrAccountType.INVASION,
                    RwrAccount.username.in_(all_player_names)
                ).all()

                rwr_accounts_by_username = {rwr_account.username: rwr_account for rwr_account in existing_rwr_accounts}

                # Remove players already having an RWR account and that are already up-to-date in the DB to prevent saving duplicate stats
                for player in players:
                    username = player[0] # FIXME Username isn't properly encoded, try to decode it to unicode

                    if username in rwr_accounts_by_username and rwr_accounts_by_username[username].updated_at.floor('day') >= now:
                        players.remove(player)

                # Create RWR accounts if they do not exists / touch the updated_at timestamp if they exists
                for player in players:
                    username = player[0] # FIXME Username isn't properly encoded, try to decode it to unicode

                    if username not in rwr_accounts_by_username:
                        rwr_account = RwrAccount()

                        rwr_account.username = username
                        rwr_account.type = RwrAccountType.INVASION

                        rwr_accounts_by_username[username] = rwr_account
                    else:
                        rwr_account = rwr_accounts_by_username[username]

                        rwr_account.updated_at = arrow.utcnow().floor('minute')

                    db.session.add(rwr_account)

                db.session.commit()

                # Create all the RwrAccountStat objects for each players
                all_rwr_accounts_stat = []

                for player in players:
                    username = player[0] # FIXME Username isn't properly encoded, try to decode it to unicode

                    rwr_account_stat = RwrAccountStat()

                    rwr_account_stat.leaderboard_position = leaderboard_position
                    rwr_account_stat.xp = int(player[1])
                    rwr_account_stat.kills = int(player[3])
                    rwr_account_stat.deaths = int(player[4])
                    rwr_account_stat.time_played = int(player[2]) * 60
                    rwr_account_stat.longest_kill_streak = int(player[5])
                    rwr_account_stat.targets_destroyed = int(player[6])
                    rwr_account_stat.vehicles_destroyed = int(player[7])
                    rwr_account_stat.soldiers_healed = int(player[8])
                    rwr_account_stat.teamkills = int(player[9])
                    rwr_account_stat.distance_moved = round(int(player[10]) / 1000, 1)
                    rwr_account_stat.shots_fired = int(player[10])
                    rwr_account_stat.throwables_thrown = int(player[12])
                    rwr_account_stat.created_at = created_at
                    rwr_account_stat.rwr_account_id = rwr_accounts_by_username[username].id

                    rwr_account_stat.compute_hash()

                    all_rwr_accounts_stat.append(rwr_account_stat)

                    leaderboard_position += 1

                # Remove all RwrAccountStat objects already existing in the DB (to prevent duplicates when stats didn't changed)
                all_rwr_accounts_stat_hashes = [rwr_account_stat.hash for rwr_account_stat in all_rwr_accounts_stat]

                already_existing_rwr_accounts_stats = RwrAccountStat.query.filter(
                    RwrAccountStat.hash.in_(all_rwr_accounts_stat_hashes)
                ).all()

                for already_existing_rwr_account_stats in already_existing_rwr_accounts_stats:
                    for rwr_account_stat in all_rwr_accounts_stat:
                        if already_existing_rwr_account_stats.hash == rwr_account_stat.hash:
                            all_rwr_accounts_stat.remove(rwr_account_stat)

                # Finally save stats for eligible  players
                db.session.add_all(all_rwr_accounts_stat)
                db.session.commit()

                start += chunks

    click.secho('Done', fg='green')
