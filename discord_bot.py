from rwrs import app
import disco.util.logging
import disco.client
import disco.bot


class RwrsBotPlugin(disco.bot.Plugin):
    @disco.bot.Plugin.command('ping')
    def on_ping_command(self, event):
        event.msg.reply('Pong!')


class DiscordBot:
    def __init__(self):
        disco.util.logging.setup_logging(level='DEBUG')

        self._init_client()
        self._init_bot()

    def _init_client(self):
        self.client_config = disco.client.ClientConfig()
        self.client_config.token = app.config['DISCORD_BOT_TOKEN']

        self.client = disco.client.Client(self.client_config)

    def _init_bot(self):
        self.bot_config = disco.bot.BotConfig()
        self.bot_config.commands_require_mention = False

        self.bot = disco.bot.Bot(self.client, self.bot_config)
        self.bot.add_plugin(RwrsBotPlugin)

    def run(self):
        self.bot.run_forever()
