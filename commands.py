from rwrs import app, db, cache
import models
import click
import rwr


@app.cli.command()
def create_database():
    """Delete then create all the database tables."""
    if not click.confirm('Are you sure?'):
        app.logger.info('Aborted')

        return

    app.logger.info('Dropping everything')

    db.drop_all()

    app.logger.info('Creating tables')

    db.create_all()

    app.logger.info('Done')


@app.cli.command()
def cc():
    """Clear the cache."""
    cache.clear()

    app.logger.info('Done')


@app.cli.command()
def get_servers_player_count():
    """Store the number of players on each servers."""
    app.logger.info('Getting servers list')

    scraper = rwr.DataScraper()

    servers = scraper.get_servers()

    for server in servers:
        app.logger.info('  {} ({}, {})'.format(server.name, server.players.current, server.ip_and_port))

        server_player_count = models.ServerPlayerCount()
        server_player_count.ip = server.ip
        server_player_count.port = server.port
        server_player_count.count = server.players.current

        db.session.add(server_player_count)

    app.logger.info('Persisting to database')

    db.session.commit()

    app.logger.info('Done')


@app.cli.command()
def clean_servers_player_count():
    """Delete old servers player count."""
    app.logger.info('Deleting old data')

    old_entries = models.ServerPlayerCount.query.get_old_entries()

    for old_entry in old_entries:
        db.session.delete(old_entry)

    app.logger.info('Persisting to database')

    db.session.commit()

    app.logger.info('Done')


@app.cli.command()
@click.option('--gamedir', '-g', help='Game root directory')
def extract_ranks_images(gamedir):
    """Extract ranks images from RWR."""
    context = click.get_current_context()

    if not gamedir:
        click.echo(extract_ranks_images.get_help(context))
        context.exit()

    app.logger.info('Extraction started')

    extractor = rwr.RanksImageExtractor(gamedir, app.config['RANKS_IMAGES_DIR'])
    extractor.extract()

    app.logger.info('Done')


@app.cli.command()
@click.option('--gamedir', '-g', help='Game root directory')
def extract_minimaps(gamedir):
    """Extract minimaps from RWR."""
    context = click.get_current_context()

    if not gamedir:
        click.echo(extract_minimaps.get_help(context))
        context.exit()

    app.logger.info('Extraction started')

    extractor = rwr.MinimapsImageExtractor(gamedir, app.config['MINIMAPS_IMAGES_DIR'])
    extractor.extract()

    app.logger.info('Done')
