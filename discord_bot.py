from disco.types.message import MessageEmbed
from disco.util.logging import setup_logging
from disco.client import Client, ClientConfig
from disco.bot import Bot, Plugin
from models import RwrRootServer
from gevent import monkey
from flask import url_for
from rwrs import app
import rwr.constants
import rwr.scraper
import rwr.utils
import steam_api
import helpers
import logging


monkey.patch_all()

with open('discord_bot.md', 'r', encoding='utf-8') as f:
    HELP_CONTENT = f.read()

VALID_PLAYER_SORTS = {
    'score': {'name': 'score', 'value': rwr.constants.PlayersSort.SCORE, 'getter': lambda player: player.score_display},
    'xp': {'name': 'experience', 'value': rwr.constants.PlayersSort.XP, 'getter': lambda player: player.xp_display},
    'kills': {'name': 'kills', 'value': rwr.constants.PlayersSort.KILLS, 'getter': lambda player: player.kills_display},
    'deaths': {'name': 'deaths', 'value': rwr.constants.PlayersSort.DEATHS, 'getter': lambda player: player.deaths_display},
    'ratio': {'name': 'K/D ratio', 'value': rwr.constants.PlayersSort.KD_RATIO, 'getter': lambda player: player.kd_ratio},
    'time': {'name': 'time played', 'value': rwr.constants.PlayersSort.TIME_PLAYED, 'getter': lambda player: helpers.humanize_seconds_to_hours(player.time_played)},
    'streak': {'name': 'longest kill streak', 'value': rwr.constants.PlayersSort.LONGEST_KILL_STREAK, 'getter': lambda player: player.longest_kill_streak_display},
    'tk': {'name': 'teamkills', 'value': rwr.constants.PlayersSort.TEAMKILLS, 'getter': lambda player: player.teamkills_display},
    'heals': {'name': 'soldiers healed', 'value': rwr.constants.PlayersSort.SOLDIERS_HEALED, 'getter': lambda player: player.soldiers_healed_display},
    'shots': {'name': 'shots fired', 'value': rwr.constants.PlayersSort.SHOTS_FIRED, 'getter': lambda player: player.shots_fired_display},
    'distance': {'name': 'distance moved (km)', 'value': rwr.constants.PlayersSort.DISTANCE_MOVED, 'getter': lambda player: player.distance_moved},
    'throws': {'name': 'throwables thrown', 'value': rwr.constants.PlayersSort.THROWABLES_THROWN, 'getter': lambda player: player.throwables_thrown_display},
    'vehicles': {'name': 'vehicles destroyed', 'value': rwr.constants.PlayersSort.VEHICLES_DESTROYED, 'getter': lambda player: player.vehicles_destroyed_display},
    'targets': {'name': 'targets destroyed', 'value': rwr.constants.PlayersSort.TARGETS_DESTROYED, 'getter': lambda player: player.targets_destroyed_display},
}

EMBED_COLOR = 10800919 # The well-known primary RWRS color #A4CF17, in the decimal format
PLAYERS_LIMIT = 24
SERVERS_LIMIT = 10


class RwrsDiscoBotPlugin(Plugin):
    """The RWRS Disco Bot plugin."""
    def load(self, ctx):
        super(RwrsDiscoBotPlugin, self).load(ctx)

        self.rwr_scraper = rwr.scraper.DataScraper()
        self.steam_api_client = steam_api.Client(app.config['STEAM_API_KEY'])

    @Plugin.command('help')
    def on_help_command(self, event):
        """Get help about the bot."""
        event.msg.reply(HELP_CONTENT)

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

        event.msg.reply('Here\'s stats for **{}** on **{}** ranked servers:'.format(player.username, player.database_name), embed=self._create_player_message_embed(player))

    @Plugin.command('whereis', '<username:str>', aliases=['where is', 'where'])
    def on_whereis_command(self, event, username):
        """Displays information about the server the specified player is currently playing on."""
        username = username.upper()

        server = self.rwr_scraper.get_current_server_of_player(username)

        if not server:
            event.msg.reply('Nah, this player isn\'t currently playing online :disappointed:')

            return

        event.msg.reply('I found **{}** playing on **{}**:'.format(username, server.name), embed=self._create_server_message_embed(server))

    @Plugin.command('server', '<name:str>')
    def on_server_command(self, event, name):
        """Displays information about the specified server."""
        server = self.rwr_scraper.get_server_by_name(name)

        if not server:
            event.msg.reply('Sorry mate, I didn\'t find this server :disappointed:')

            return

        event.msg.reply('Here\'s information about **{}**:'.format(server.name), embed=self._create_server_message_embed(server))

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
    @Plugin.parser.add_argument('--ranked', action='store_const', const='yes')
    @Plugin.parser.add_argument('--not-full', action='store_const', const='yes')
    def on_servers_command(self, event, args):
        """Displays the first 10 currently active servers."""
        servers = self.rwr_scraper.filter_servers(
            limit=SERVERS_LIMIT,
            not_empty='yes',
            not_full=args.not_full,
            ranked=args.ranked
        )

        filters = []

        if args.not_full:
            filters.append('not full')

        if args.ranked:
            filters.append('ranked')

        filters_string = ', ' + ', '.join(filters) if filters else ''

        response = [
            'Here sir, the first {} currently active{} servers:\n'.format(SERVERS_LIMIT, filters_string)
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
    @Plugin.parser.add_argument('sort', choices=VALID_PLAYER_SORTS.keys(), nargs='?', default='score')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_top_command(self, event, args):
        """Displays the top 15 players."""
        embed = self._create_base_message_embed()

        players = self.rwr_scraper.get_players(
            args.database,
            limit=PLAYERS_LIMIT,
            sort=VALID_PLAYER_SORTS[args.sort]['value']
        )

        for player in players:
            embed.add_field(
                name='#{} {}'.format(player.position_display, player.username),
                value=VALID_PLAYER_SORTS[args.sort]['getter'](player),
                inline=True
            )

        event.msg.reply('Everyone! The top {} **{}** players, ordered by {} :military_medal:'.format(
            PLAYERS_LIMIT,
            rwr.utils.get_database_name(args.database),
            VALID_PLAYER_SORTS[args.sort]['name']
        ), embed=embed)

    @Plugin.command('pos', aliases=['position', 'ranking'], parser=True)
    @Plugin.parser.add_argument('username')
    @Plugin.parser.add_argument('sort', choices=VALID_PLAYER_SORTS.keys(), nargs='?', default='score')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_pos_command(self, event, args):
        """Highlights the specified player in the leaderboard."""
        args.username = args.username.upper()

        players = self.rwr_scraper.get_players(
            args.database,
            limit=PLAYERS_LIMIT,
            target=args.username,
            sort=VALID_PLAYER_SORTS[args.sort]['value']
        )

        if not players:
            event.msg.reply('Sorry dude, this player don\'t exist :confused:')

            return

        embed = self._create_base_message_embed()

        for player in players:
            embed.add_field(
                name='{}#{} {}'.format('➡️ ' if player.username == args.username else '', player.position, player.username),
                value=VALID_PLAYER_SORTS[args.sort]['getter'](player),
                inline=True
            )

        event.msg.reply('Here\'s the position of **{}** on the **{}** leaderboard, ordered by {}:'.format(
            args.username,
            rwr.utils.get_database_name(args.database),
            VALID_PLAYER_SORTS[args.sort]['name']
        ), embed=embed)

    def _create_player_message_embed(self, player):
        """Create a RWRS player rich Discord message."""
        embed = self._create_base_message_embed()

        embed.url = player.link_absolute

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
                player.xp_display
            ),
            inline=True
        )

        embed.add_field(
            name='Next rank',
            value='{}\n{} XP'.format(
                player.next_rank.name,
                helpers.humanize_integer(player.next_rank.xp)
            ) if player.next_rank else 'Highest possible\nrank reached',
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
            value=player.kills_display,
            inline=True
        )

        embed.add_field(
            name='Deaths',
            value=player.deaths_display,
            inline=True
        )

        embed.add_field(
            name='K/D ratio',
            value=player.kd_ratio,
            inline=True
        )

        embed.add_field(
            name='Score',
            value=player.score_display,
            inline=True
        )

        embed.add_field(
            name='Time played',
            value=helpers.humanize_seconds_to_hours(player.time_played) + ' (' + helpers.humanize_seconds_to_days(player.time_played) + ')' if player.display_time_played_in_days else helpers.humanize_seconds_to_hours(player.time_played),
            inline=True
        )

        if player.playing_on_server:
            embed.set_footer(text='🖱 Playing on {} ({})'.format(
                player.playing_on_server.name_display,
                player.playing_on_server.summary
            ))

        return embed

    def _create_server_message_embed(self, server):
        """Create a RWRS server rich Discord message."""
        embed = self._create_base_message_embed()

        embed.url = server.link_absolute
        embed.description = server.steam_join_link.replace(' ', '%20')

        if server.players.list:
            embed.add_field(
                name='Players list',
                value=', '.join(server.players.list)
            )

        if server.map.has_preview:
            embed.set_thumbnail(
                url=server.map.preview_absolute
            )

        embed.add_field(
            name='Players count',
            value='{}/{}'.format(server.players.current, server.players.max),
            inline=True
        )

        embed.add_field(
            name='Map',
            value=server.map.name_display,
            inline=True
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

        if server.location.country_code:
            embed.add_field(
                name='Location',
                value=':flag_{}: {}'.format(
                    server.location.country_code,
                    server.location.text
                ),
                inline=True
            )

        if server.is_ranked:
            embed.set_footer(text='⭐️ Ranked {} server'.format(server.database_name))

        return embed

    def _create_base_message_embed(self):
        """Create a rich Discord message."""
        embed = MessageEmbed()

        embed.color = EMBED_COLOR

        return embed


class DiscordBot:
    """The high-level class that wraps the RWRS Discord bot logic."""
    def __init__(self):
        setup_logging(level=logging.WARNING)

        self.client_config = ClientConfig()
        self.client_config.token = app.config['DISCORD_BOT_TOKEN']

        self.client = Client(self.client_config)

        self.bot = Bot(self.client)
        self.bot.add_plugin(RwrsDiscoBotPlugin)

    def run(self):
        """Actually run the RWRS Discord bot."""
        self.bot.run_forever()
