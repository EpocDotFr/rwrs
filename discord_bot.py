from disco.client import Client, ClientConfig
from disco.util.logging import setup_logging
from disco.bot import Bot, BotConfig, Plugin
from rwrs import app
import rwr.scraper


class RwrsDiscoBotPlugin(Plugin):
    """The RWRS Disco Bot plugin."""
    @Plugin.command('rank <username:str> [<database:str>]')
    def on_rank_command(self, event, username, database='invasion'):
        """Get rank information about the specified player."""
        scraper = rwr.scraper.DataScraper()

        player = scraper.search_player_by_username(username, database)

        if not player:
            event.msg.reply('D\'oh, I didn\'t found this player.')
        else:
            event.msg.reply(player.username) # TODO

    @Plugin.command('stats <username:str> [<database:str>]')
    def on_stats_command(self, event, username, database='invasion'):
        """Get stats about the specified player."""
        scraper = rwr.scraper.DataScraper()

        player = scraper.search_player_by_username(username, database)

        if not player:
            event.msg.reply('Sorry dude, this player don\'t exist.')
        else:
            event.msg.reply(player.username) # TODO

    @Plugin.command('whereis <username:str>')
    def on_whereis_command(self, event, username):
        """Get information about the server the specified player is currently playing on, if any."""
        scraper = rwr.scraper.DataScraper()

        server = scraper.get_current_server_of_player(username)

        if not server:
            event.msg.reply('Nah, this player isn\'t currently online.')
        else:
            event.msg.reply(server.name) # TODO

    @Plugin.command('server <name:str>')
    def on_server_command(self, event, name):
        """Get information about the specified server."""
        scraper = rwr.scraper.DataScraper()

        server = scraper.get_server_by_name(name)

        if not server:
            event.msg.reply('Sorry mate, I didn\'t found this server.')
        else:
            event.msg.reply(server.name) # TODO


class DiscordBot:
    """The high-level class that wraps the RWRS Discord bot logic."""
    def __init__(self):
        setup_logging(level='DEBUG')

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
