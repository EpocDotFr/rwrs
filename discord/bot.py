from disco.client import Client, ClientConfig
from disco.util.logging import setup_logging
from disco.bot import Bot, Plugin
from models import RwrRootServer
from . import constants, utils
from flask import url_for
from gevent import monkey
from rwrs import app
import rwr.scraper
import rwr.utils
import steam_api
import logging

monkey.patch_all()


class RwrsBotCore(Plugin):
    """The RWRS Disco Bot plugin."""
    def load(self, ctx):
        super(RwrsBotCore, self).load(ctx)

        self.rwr_scraper = rwr.scraper.DataScraper()
        self.steam_api_client = steam_api.Client(app.config['STEAM_API_KEY'])

    @Plugin.command('help')
    def on_help_command(self, event):
        """Get help about the bot."""
        event.msg.reply(constants.HELP_CONTENT)

    @Plugin.command('info')
    def on_info_command(self, event):
        """Get information about the bot."""
        info = [
            'ℹ️ Hi! I was created by <@66543750725246976> - the guy behind https://rwrstats.com - around the beginning of March 2018.',
            'Like the rwrstats.com website, my brain is powered by the Python programming language.',
            'P.S. You look beautiful today.'
        ]

        event.msg.reply('\n'.join(info))

    @Plugin.command('stats', aliases=['statistics'], parser=True)
    @Plugin.parser.add_argument('username')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_stats_command(self, event, args):
        """Displays stats about the specified player."""
        player = self.rwr_scraper.search_player_by_username(args.database, args.username)

        if not player:
            event.msg.reply('Sorry dude, this player don\'t exist :confused:')

            return

        servers = self.rwr_scraper.get_servers()

        player.set_playing_on_server(servers)

        event.msg.reply('Here\'s stats for **{}** on **{}** ranked servers:'.format(player.username, player.database_name), embed=utils.create_player_message_embed(player))

    @Plugin.command('whereis', '<username:str>', aliases=['where is', 'where'])
    def on_whereis_command(self, event, username):
        """Displays information about the server the specified player is currently playing on."""
        username = username.upper()

        server = self.rwr_scraper.get_current_server_of_player(username)

        if not server:
            event.msg.reply('Nah, this player isn\'t currently playing online :disappointed:')

            return

        event.msg.reply('I found **{}** playing on **{}**:'.format(username, server.name), embed=utils.create_server_message_embed(server))

    @Plugin.command('server', '<name:str>')
    def on_server_command(self, event, name):
        """Displays information about the specified server."""
        server = self.rwr_scraper.get_server_by_name(name)

        if not server:
            event.msg.reply('Sorry mate, I didn\'t find this server :disappointed:')

            return

        event.msg.reply('Here\'s information about **{}**:'.format(server.name), embed=utils.create_server_message_embed(server))

    @Plugin.command('now', aliases=['currently'])
    def on_now_command(self, event):
        """Displays numbers about the current players and servers."""
        answer = [
            'There\'s currently **{total_players}** player{total_players_plural} in total. **{online_players}** of them {online_players_plural} playing multiplayer online.',
            'There\'s also **{total_servers}** online multiplayer servers, **{active_servers}** of which {active_servers_plural} active :wink:'
        ]

        total_players = self.steam_api_client.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])
        online_players, active_servers, total_servers = self.rwr_scraper.get_counters()

        event.msg.reply('\n'.join(answer).format(
            total_players=total_players,
            total_players_plural='s' if total_players > 1 else '',
            online_players=online_players,
            online_players_plural='are' if online_players > 1 else 'is',
            total_servers=total_servers,
            total_servers_plural='s' if total_servers > 1 else '',
            active_servers=active_servers,
            active_servers_plural='are' if active_servers > 1 else 'is'
        ))

    @Plugin.command('status')
    def on_status_command(self, event):
        """Displays the current status of the online multiplayer."""
        is_everything_ok, servers_statuses = RwrRootServer.get_data_for_display()

        if is_everything_ok:
            event.msg.reply(':white_check_mark: Online multiplayer is working fine. Go play with others!')
        else:
            with app.app_context():
                event.msg.reply(':warning: Looks like online multiplayer is encountering issues.\nFor details, head over here: {}'.format(url_for('online_multiplayer_status', _external=True)))

    @Plugin.command('servers', parser=True)
    @Plugin.parser.add_argument('type', choices=constants.VALID_SERVER_TYPES.keys(), nargs='?', default=None)
    @Plugin.parser.add_argument('--ranked', action='store_const', const='yes')
    def on_servers_command(self, event, args):
        """Displays the first 10 currently active servers with room."""
        servers = self.rwr_scraper.filter_servers(
            limit=constants.SERVERS_LIMIT,
            not_empty='yes',
            not_full='yes',
            ranked=args.ranked,
            type=constants.VALID_SERVER_TYPES[args.type] if args.type else 'any'
        )

        if not servers:
            event.msg.reply('Well, looks like no servers are matching :disappointed:')

            return

        filters = []

        if args.ranked:
            filters.append('ranked')

        if args.type:
            filters.append(rwr.constants.SERVER_TYPES[constants.VALID_SERVER_TYPES[args.type]])

        filters_string = ', ' + ', '.join(filters) if filters else ''

        response = [
            'Here sir, the first {} currently active{} servers with room:\n'.format(constants.SERVERS_LIMIT, filters_string)
        ]

        for server in servers:
            response.append('{}`{}/{}` **{}** ({} • {})\n{}\n'.format(
                ':flag_' + server.location.country_code + ': ' if server.location.country_code else '',
                server.players.current,
                server.players.max,
                server.name_display,
                server.type_name,
                server.map.name_display,
                server.steam_join_link.replace(' ', '%20')
            ))

        event.msg.reply('\n'.join(response))

    @Plugin.command('top', aliases=['leaderboard'], parser=True)
    @Plugin.parser.add_argument('sort', choices=constants.VALID_PLAYER_SORTS.keys(), nargs='?', default='score')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_top_command(self, event, args):
        """Displays the top 15 players."""
        embed = utils.create_base_message_embed()

        players = self.rwr_scraper.get_players(
            args.database,
            limit=constants.PLAYERS_LIMIT,
            sort=constants.VALID_PLAYER_SORTS[args.sort]['value']
        )

        for player in players:
            embed.add_field(
                name='#{} {}'.format(player.position_display, player.username),
                value=constants.VALID_PLAYER_SORTS[args.sort]['getter'](player),
                inline=True
            )

        event.msg.reply('Everyone! The top {} **{}** players, ordered by {} :military_medal:'.format(
            constants.PLAYERS_LIMIT,
            rwr.utils.get_database_name(args.database),
            constants.VALID_PLAYER_SORTS[args.sort]['name']
        ), embed=embed)

    @Plugin.command('pos', aliases=['position', 'ranking'], parser=True)
    @Plugin.parser.add_argument('username')
    @Plugin.parser.add_argument('sort', choices=constants.VALID_PLAYER_SORTS.keys(), nargs='?', default='score')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_pos_command(self, event, args):
        """Highlights the specified player in the leaderboard."""
        args.username = args.username.upper()

        players = self.rwr_scraper.get_players(
            args.database,
            limit=constants.PLAYERS_LIMIT,
            target=args.username,
            sort=constants.VALID_PLAYER_SORTS[args.sort]['value']
        )

        if not players:
            event.msg.reply('Sorry dude, this player don\'t exist :confused:')

            return

        embed = utils.create_base_message_embed()

        for player in players:
            embed.add_field(
                name='{}#{} {}'.format('➡️ ' if player.username == args.username else '', player.position, player.username),
                value=constants.VALID_PLAYER_SORTS[args.sort]['getter'](player),
                inline=True
            )

        event.msg.reply('Here\'s the position of **{}** on the **{}** leaderboard, ordered by {}:'.format(
            args.username,
            rwr.utils.get_database_name(args.database),
            constants.VALID_PLAYER_SORTS[args.sort]['name']
        ), embed=embed)

    @Plugin.command('compare', parser=True)
    @Plugin.parser.add_argument('source_username')
    @Plugin.parser.add_argument('target_username')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_compare_command(self, event, args):
        args.source_username = args.source_username.upper()
        args.target_username = args.target_username.upper()

        source_player = self.rwr_scraper.search_player_by_username(args.database, args.source_username)

        if not source_player:
            event.msg.reply('I\'m sorry, I cannot find **{}** :disappointed:'.format(args.source_username))

            return

        target_player = self.rwr_scraper.search_player_by_username(args.database, args.target_username)

        if not target_player:
            event.msg.reply('Nah, I cannot find **{}** :disappointed:'.format(args.target_username))

            return

        embed = utils.create_base_message_embed()

        # TODO

        event.msg.reply('At your service, comparison of **{}** and **{}** on the **{}** leaderboard:'.format(
            args.source_username,
            args.target_username,
            rwr.utils.get_database_name(args.database)
        ), embed=embed)


class RwrsBot:
    """The high-level class that wraps the RWRS Discord bot logic."""
    def __init__(self):
        setup_logging(level=logging.WARNING)

        self.client_config = ClientConfig()
        self.client_config.token = app.config['DISCORD_BOT_TOKEN']

        self.client = Client(self.client_config)

        self.bot = Bot(self.client)
        self.bot.add_plugin(RwrsBotCore)

    def run(self):
        """Actually run the RWRS Discord bot."""
        self.bot.run_forever()
