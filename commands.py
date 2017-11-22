from rwrs import app, db, cache
from models import *
import click
import rwr


@app.cli.command()
def create_database():
    """Delete then create all the database tables."""
    if not click.confirm('Are you sure?'):
        click.secho('Aborted', fg='red')

        return

    click.echo('Dropping everything')

    db.drop_all()

    click.echo('Creating tables')

    db.create_all()

    click.secho('Done', fg='green')


@app.cli.command()
def cc():
    """Clear the cache."""
    click.echo('Clearing cache')

    cache.clear()

    click.secho('Done', fg='green')


@app.cli.command()
def get_servers_player_count():
    """Store the number of players on each servers."""
    scraper = rwr.DataScraper()

    click.echo('Clearing  cache')

    cache.delete_memoized(rwr.DataScraper.get_servers)
    cache.delete_memoized(ServerPlayerCount.server_players_data)
    cache.delete_memoized(ServerPlayerCount.servers_data)

    click.echo('Getting servers list')

    servers = scraper.get_servers()

    for server in servers:
        click.echo('  {} ({}, {})'.format(server.name, server.players.current, server.ip_and_port))

        server_player_count = ServerPlayerCount()
        server_player_count.ip = server.ip
        server_player_count.port = server.port
        server_player_count.count = server.players.current

        db.session.add(server_player_count)

    click.echo('Persisting to database')

    db.session.commit()

    click.secho('Done', fg='green')


@app.cli.command()
def clean_servers_player_count():
    """Delete old servers player count."""
    click.echo('Deleting old data')

    old_entries = ServerPlayerCount.query.get_old_entries()

    for old_entry in old_entries:
        db.session.delete(old_entry)

    click.echo('Persisting to database')

    db.session.commit()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--gamedir', '-g', help='Game root directory')
def extract_ranks_images(gamedir):
    """Extract ranks images from RWR."""
    context = click.get_current_context()

    if not gamedir:
        click.echo(extract_ranks_images.get_help(context))
        context.exit()

    click.echo('Extraction started')

    extractor = rwr.RanksImageExtractor(gamedir, app.config['RANKS_IMAGES_DIR'])
    extractor.extract()

    click.secho('Done', fg='green')


@app.cli.command()
@click.option('--gamedir', '-g', help='Game root directory')
def extract_minimaps(gamedir):
    """Extract minimaps from RWR."""
    context = click.get_current_context()

    if not gamedir:
        click.echo(extract_minimaps.get_help(context))
        context.exit()

    click.echo('Extraction started')

    extractor = rwr.MinimapsImageExtractor(gamedir, app.config['MINIMAPS_IMAGES_DIR'])
    extractor.extract()

    click.secho('Done', fg='green')
