from disco.types.message import MessageEmbed
from disco.util.logging import setup_logging
from disco.client import Client, ClientConfig
from disco.bot import Bot, BotConfig, Plugin
from gevent import monkey
from flask import url_for
from rwrs import app
import rwr.scraper
import rwr.utils
import helpers
import logging


monkey.patch_all()


class RwrsDiscoBotPlugin(Plugin):
    """The RWRS Disco Bot plugin."""
    def load(self, ctx):
        super(RwrsDiscoBotPlugin, self).load(ctx)

        self.rwr_scraper = rwr.scraper.DataScraper()

    @Plugin.command('rank', '<username:str> [servers:str]')
    def on_rank_command(self, event, username, servers='invasion'): # TODO Limit servers to invasion|pacific
        """Get rank information about the specified player."""
        player = self.rwr_scraper.search_player_by_username(servers, username)

        if not player:
            event.msg.reply('D\'oh, I didn\'t found this player :disappointed:')

            return

        embed = self.create_base_message_embed()

        embed.url = player.link_absolute
        embed.title = 'Players › {} › {} › Rank'.format(rwr.utils.get_database_name(servers), player.username)
        embed.description = 'Rank information of {} on {} RWR ranked servers.'.format(player.username, rwr.utils.get_database_name(servers))

        embed.add_field(
            name='Current rank',
            value='{}\n\n{} XP'.format(
                player.rank.name,
                helpers.humanize_integer(player.xp)
            ),
            inline=True
        )

        embed.add_field(
            name='Next rank progression',
            value='{}%\n\n{} XP remaining'.format(
                player.xp_percent_completion_to_next_rank,
                helpers.humanize_integer(player.xp_to_next_rank)
            ) if player.next_rank else 'N/A',
            inline=True
        )

        embed.add_field(
            name='Next rank',
            value='{}\n\n{} XP'.format(
                player.next_rank.name,
                helpers.humanize_integer(player.next_rank.xp)
            ) if player.next_rank else 'Highest possible rank reached',
            inline=True
        )

        event.msg.reply('There ya go :thumbsup:', embed=embed)

    @Plugin.command('stats', '<username:str> [servers:str]')
    def on_stats_command(self, event, username, servers='invasion'): # TODO Limit servers to invasion|pacific
        """Get stats about the specified player."""
        player = self.rwr_scraper.search_player_by_username(servers, username)

        if not player:
            event.msg.reply('Sorry dude, this player don\'t exist :confused:')

            return

        embed = self.create_base_message_embed()

        embed.url = player.link_absolute
        embed.title = 'Players › {} › {} › Stats'.format(rwr.utils.get_database_name(servers), player.username)
        embed.description = 'Statistics of {} on {} RWR ranked servers.'.format(player.username, rwr.utils.get_database_name(servers))

        # TODO Add stats fields

        event.msg.reply('At your service :muscle:', embed=embed)

    @Plugin.command('whereis', '<username:str>')
    def on_whereis_command(self, event, username):
        """Get information about the server the specified player is currently playing on."""
        server = self.rwr_scraper.get_current_server_of_player(username)

        if not server:
            event.msg.reply('Nah, this player isn\'t currently online :confused:')

            return

        event.msg.reply('I found {} playing on this server:'.format(username), embed=self.create_server_message_embed(server))

    @Plugin.command('server', '<name:str>')
    def on_server_command(self, event, name):
        """Get information about the specified server."""
        server = self.rwr_scraper.get_server_by_name(name)

        if not server:
            event.msg.reply('Sorry mate, I didn\'t found this server :disappointed:')

            return

        event.msg.reply('My pleasure :smirk:', embed=self.create_server_message_embed(server))

    def create_server_message_embed(self, server):
        """Create a RWRS server rich Discord message."""
        embed = self.create_base_message_embed()

        embed.url = server.link_absolute
        embed.title = server.name

        return embed

    def create_base_message_embed(self):
        """Create a rich Discord message."""
        embed = MessageEmbed()

        embed.set_author(
            name='Running With Rifles Stats (RWRS)',
            url='https://rwrstats.com/',
            icon_url=url_for('static', filename='images/icon_dark_256.png', _external=True)
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
        """Run the RWRS Discord bot."""
        self.bot.run_forever()
