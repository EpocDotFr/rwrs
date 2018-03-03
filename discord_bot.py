from disco.types.message import MessageEmbed
from disco.util.logging import setup_logging
from disco.client import Client, ClientConfig
from disco.bot import Bot, BotConfig, Plugin
from models import RwrRootServer
from gevent import monkey
from flask import url_for
from rwrs import app
import rwr.constants
import rwr.scraper
import steam_api
import helpers
import logging


monkey.patch_all()


class RwrsDiscoBotPlugin(Plugin):
    """The RWRS Disco Bot plugin."""
    def load(self, ctx):
        super(RwrsDiscoBotPlugin, self).load(ctx)

        self.rwr_scraper = rwr.scraper.DataScraper()
        self.steam_api_client = steam_api.Client(app.config['STEAM_API_KEY'])

    @Plugin.command('stats', parser=True)
    @Plugin.parser.add_argument('username')
    @Plugin.parser.add_argument('database', choices=rwr.constants.PLAYERS_LIST_DATABASES.keys(), nargs='?', default='invasion')
    def on_stats_command(self, event, args):
        """Get stats about the specified player."""
        player = self.rwr_scraper.search_player_by_username(args.database, args.username)

        if not player:
            event.msg.reply('Sorry dude, this player don\'t exist :confused:')

            return

        servers = self.rwr_scraper.get_servers()

        player.set_playing_on_server(servers)

        event.msg.reply('There ya go :thumbsup:', embed=self.create_player_message_embed(player))

    @Plugin.command('whereis', '<username:str>')
    def on_whereis_command(self, event, username):
        """Get information about the server the specified player is currently playing on."""
        server = self.rwr_scraper.get_current_server_of_player(username)

        if not server:
            event.msg.reply('Nah, this player isn\'t currently playing online :confused:')

            return

        event.msg.reply('I found **{}** playing on this server:'.format(username), embed=self.create_server_message_embed(server))

    @Plugin.command('server', '<name:str>')
    def on_server_command(self, event, name):
        """Get information about the specified server."""
        server = self.rwr_scraper.get_server_by_name(name)

        if not server:
            event.msg.reply('Sorry mate, I didn\'t find this server :disappointed:')

            return

        event.msg.reply('At your service :muscle:', embed=self.create_server_message_embed(server, with_players_list=True))

    @Plugin.command('now')
    def on_now_command(self, event):
        """Get numbers about the current RWR players and servers."""
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
        """Get status about the RWR online multiplayer architecture."""
        is_everything_ok, servers_statuses = RwrRootServer.get_data_for_display()

        if is_everything_ok:
            event.msg.reply('✅ Online multiplayer is working fine. Go play with others!')
        else:
            with app.app_context():
                event.msg.reply('⚠️ Looks like online multiplayer is encountering issues.\nFor details, head over here: {}'.format(url_for('online_multiplayer_status', _external=True)))

    @Plugin.command('servers')
    def on_servers_command(self, event):
        """Return the top currently active RWR servers."""
        limit = 10

        embed = self.create_base_message_embed()

        with app.app_context():
            embed.url = url_for('servers_list', _external=True)

        embed.title = 'Servers'

        servers = self.rwr_scraper.filter_servers(limit=limit, not_empty='yes', not_full='yes')

        for server in servers:
            embed.add_field(
                name='{}{}'.format(':flag_' + server.location.country_code + ': ' if server.location.country_code else '', server.name_display),
                value=server.summary
            )

        event.msg.reply('Here sir, the top {} currently active servers:'.format(limit), embed=embed)

    def create_player_message_embed(self, player):
        """Create a RWRS player rich Discord message."""
        embed = self.create_base_message_embed()

        embed.url = player.link_absolute
        embed.title = 'Players › {} › {}'.format(player.database_name, player.username)

        if player.is_me:
            embed.description = ':wave: Hey, I\'m the creator of RWRS and this bot! Glad to see you\'re using it.'
        elif player.is_contributor:
            embed.description = ':v: This player contributed in a way or another to RWRS. Thanks to her/him!'
        elif player.is_rwr_dev:
            embed.description = ':military_medal: Say hi to one of the Running With Rifles developers!'

        embed.set_thumbnail(
            url=player.rank.image_absolute
        )

        embed.add_field(
            name='Current rank',
            value='{}\n{} XP'.format(
                player.rank.name,
                helpers.humanize_integer(player.xp)
            ),
            inline=True
        )

        embed.add_field(
            name='Next rank',
            value='{}\n{} XP'.format(
                player.next_rank.name,
                helpers.humanize_integer(player.next_rank.xp)
            ) if player.next_rank else 'Highest possible rank reached',
            inline=True
        )

        if player.next_rank:
            embed.add_field(
                name='Next rank progression',
                value='{}% - {} XP remaining'.format(
                    player.xp_percent_completion_to_next_rank,
                    helpers.humanize_integer(player.xp_to_next_rank)
                )
            )

        embed.add_field(
            name='Kills',
            value=helpers.humanize_integer(player.kills),
            inline=True
        )

        embed.add_field(
            name='Deaths',
            value=helpers.humanize_integer(player.deaths),
            inline=True
        )

        embed.add_field(
            name='K/D ratio',
            value=player.kd_ratio,
            inline=True
        )

        embed.add_field(
            name='Score',
            value=helpers.humanize_integer(player.score),
            inline=True
        )

        embed.add_field(
            name='Time played',
            value=helpers.humanize_seconds_to_hours(player.time_played) + ' (' + helpers.humanize_seconds_to_days(player.time_played) + ')',
            inline=True
        )

        if player.playing_on_server:
            embed.set_footer(text='🎮 Playing on {} ({})'.format(
                player.playing_on_server.name_display,
                player.playing_on_server.summary
            ))

        return embed

    def create_server_message_embed(self, server, with_players_list=False):
        """Create a RWRS server rich Discord message."""
        embed = self.create_base_message_embed()

        embed.url = server.link_absolute
        embed.title = 'Servers › {}'.format(server.name)
        embed.description = '[Join now]({})'.format(server.steam_join_link.replace(' ', '%20')) # FIXME Don't work

        if server.website:
            embed.description += ' • [Server website]({})'.format(server.website)

        if with_players_list and server.players.list:
            embed.add_field(
                name='Players',
                value=', '.join(server.players.list)
            )

        if server.map.has_preview:
            with app.app_context():
                embed.set_thumbnail(
                    url=url_for('static', filename='images/maps/preview/{game_type}/{map_id}.png'.format(game_type=server.type, map_id=server.map.id), _external=True)
                )

        embed.add_field(
            name='Type',
            value=server.type_name,
            inline=True
        )

        embed.add_field(
            name='Mode',
            value=server.mode_name,
            inline=True
        )

        embed.add_field(
            name='Map',
            value=server.map.name_display,
            inline=True
        )

        embed.add_field(
            name='Current players',
            value=server.players.current,
            inline=True
        )

        embed.add_field(
            name='Max players',
            value=server.players.max,
            inline=True
        )

        if server.location.country_code:
            embed.add_field(
                name='Location',
                value=':flag_{}: {}{}'.format(
                    server.location.country_code,
                    server.location.city_name + ', ' if server.location.city_name else '',
                    server.location.country_name
                ),
                inline=True
            )

        if server.is_ranked:
            embed.set_footer(text='⭐️ Ranked {} server'.format(server.database_name))

        return embed

    def create_base_message_embed(self):
        """Create a rich Discord message."""
        embed = MessageEmbed()

        with app.app_context():
            embed.set_author(
                name='Running With Rifles Stats (RWRS)',
                url=url_for('home', _external=True),
                icon_url=url_for('static', filename='images/icon_square_dark_256.png', _external=True)
            )

        embed.color = 10800919 # The well-known primary RWRS color #A4CF17, in the decimal format

        return embed


class DiscordBot:
    """The high-level class that wraps the RWRS Discord bot logic."""
    def __init__(self):
        setup_logging(level=logging.WARNING)

        self.client_config = ClientConfig()
        self.client_config.token = app.config['DISCORD_BOT_TOKEN']

        self.client = Client(self.client_config)

        self.bot_config = BotConfig()
        self.bot_config.commands_enabled = True
        self.bot_config.commands_require_mention = False
        self.bot_config.commands_prefix = '!'

        self.bot = Bot(self.client, self.bot_config)
        self.bot.add_plugin(RwrsDiscoBotPlugin)

    def run(self):
        """Actually run the RWRS Discord bot."""
        self.bot.run_forever()
