from disco.types.message import MessageEmbed
from disco.util.logging import setup_logging
from disco.client import Client, ClientConfig
from disco.bot import Bot, BotConfig, Plugin
from gevent import monkey
from flask import url_for
from rwrs import app
import rwr.constants
import rwr.scraper
import helpers
import logging


monkey.patch_all()


class RwrsDiscoBotPlugin(Plugin):
    """The RWRS Disco Bot plugin."""
    def load(self, ctx):
        super(RwrsDiscoBotPlugin, self).load(ctx)

        self.rwr_scraper = rwr.scraper.DataScraper()

    @Plugin.command('stats', '<username:str> [database:str]')
    def on_stats_command(self, event, username, database='invasion'): # TODO Limit database to invasion|pacific
        """Get stats about the specified player."""
        player = self.rwr_scraper.search_player_by_username(database, username)

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
            event.msg.reply('Sorry mate, I didn\'t found this server :disappointed:')

            return

        event.msg.reply('At your service :muscle:', embed=self.create_server_message_embed(server))

    def create_player_message_embed(self, player):
        """Create a RWRS player rich Discord message."""
        embed = self.create_base_message_embed()

        embed.url = player.link_absolute
        embed.title = 'Players › {} › {}'.format(player.database_name, player.username)

        with app.app_context():
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
            embed.set_footer(text='Currently playing online on {} ({} - {} - {}/{})'.format(
                player.playing_on_server.name_display,
                player.playing_on_server.type_name,
                player.playing_on_server.map.name_display,
                player.playing_on_server.players.current,
                player.playing_on_server.players.max
            ))

        return embed

    def create_server_message_embed(self, server):
        """Create a RWRS server rich Discord message."""
        embed = self.create_base_message_embed()

        embed.url = server.link_absolute
        embed.title = 'Servers › {}'.format(server.name_display)

        if server.map.has_preview:
            with app.app_context():
                embed.set_thumbnail(
                    url=url_for('static', filename='images/maps/preview/{game_type}/{map_id}.png'.format(game_type=server.type, map_id=server.map.id))
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

        embed.add_field(
            name='Location',
            value='TODO', # TODO Emoji of the country flag + (city) + country name
            inline=True
        )

        return embed

    def create_base_message_embed(self):
        """Create a rich Discord message."""
        embed = MessageEmbed()

        with app.app_context():
            embed.set_author(
                name='Running With Rifles Stats (RWRS)',
                url=url_for('home', _external=True),
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
