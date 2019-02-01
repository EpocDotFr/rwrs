from models import Variable, RwrAccount, RwrAccountStat
from disco.types.user import GameType, Game, Status
from disco.client import Client, ClientConfig
from disco.util.logging import setup_logging
from disco.bot import Bot, Plugin, BotConfig
from . import constants, utils
from tabulate import tabulate
from rwr.player import Player
from rwrs import app, cache
from gevent import monkey
import rwr.scraper
import rwr.utils
import logging
import helpers
import steam
import os

monkey.patch_all()


class RwrsBotDiscoPlugin(Plugin):
    """The RWRS Disco Bot plugin."""
    def load(self, ctx):
        super(RwrsBotDiscoPlugin, self).load(ctx)

        self.steamworks_api_client = steam.SteamworksApiClient(app.config['STEAM_API_KEY'])

    @Plugin.route('/ping')
    def status_check_route(self):
        return 'pong'

    @Plugin.pre_command()
    def check_guild(self, func, event, args, kwargs):
        """Check if the incoming message comes from the right Discord guild (server)."""
        if not event: # For some reason, event may be None
            return None

        if app.config['ENV'] == 'development' and not event.msg.guild: # PM on development env: cancel
            return None

        if event.msg.guild and event.msg.guild.id != app.config['DISCORD_BOT_GUILD_ID']: # Message not sent from the right guild
            return None

        return event

    @Plugin.pre_command()
    def check_under_maintenance(self, func, event, args, kwargs):
        """Check if RWRS is under maintenance, preventing any commands to be invoked if that's the case."""
        if os.path.exists('maintenance') and event.msg.author.id not in app.config['DISCORD_BOT_ADMINS']:
            event.msg.reply(':wrench: RWRS is under ongoing maintenance! Please try again later.')

            return None

        return event

    @Plugin.pre_command()
    def check_can_invoke_command(self, func, event, args, kwargs):
        """Check if the specified command is available and can be invoked by the user."""
        # If the user is not admin and if the command isn't in the public commands list
        if event.name != 'help' and event.msg.author.id not in app.config['DISCORD_BOT_ADMINS'] and event.name not in constants.AVAILABLE_PUBLIC_COMMANDS_NAMES:
            return None

        return event

    @Plugin.listen('Ready')
    def on_ready_event(self, event):
        """Performs things when the bot is ready."""
        self.client.update_presence(Status.ONLINE, Game(type=GameType.DEFAULT, name='"@rwrs help" for help', url='https://rwrstats.com/'))

    @Plugin.command('cc')
    def on_cc_command(self, event):
        """Admin command: clears the RWRS cache."""
        cache.clear()

        event.msg.reply('Cache cleared.')

    @Plugin.command('say', parser=True)
    @Plugin.parser.add_argument('message')
    def on_say_command(self, event, args):
        """Admin command: makes the bot to say something."""
        self.client.api.channels_messages_create(app.config['DISCORD_BOT_CHANNEL_ID'], args.message)

    @Plugin.command('maintenance', parser=True)
    @Plugin.parser.add_argument('action', choices=['enable', 'disable'])
    def on_maintenance_command(self, event, args):
        """Admin command: enables or disables the maintenance mode."""
        if args.action == 'enable':
            if os.path.exists('maintenance'):
                event.msg.reply('Maintenance mode already enabled.')
            else:
                open('maintenance', 'a').close()

                event.msg.reply('Maintenance mode enabled.')
        elif args.action == 'disable':
            if not os.path.exists('maintenance'):
                event.msg.reply('Maintenance mode already disabled.')
            else:
                os.remove('maintenance')

                event.msg.reply('Maintenance mode disabled.')

    @Plugin.command('set', parser=True, group='motd')
    @Plugin.parser.add_argument('message')
    def on_motd_set_command(self, event, args):
        """Admin command: sets the MOTD."""
        with open('motd', 'w', encoding='utf-8') as f:
            f.write(args.message)

        event.msg.reply('MOTD updated.')

    @Plugin.command('remove', group='motd')
    def on_motd_remove_command(self, event):
        """Admin command: removes the MOTD."""
        if not os.path.exists('motd'):
            event.msg.reply('MOTD already removed.')
        else:
            os.remove('motd')

            event.msg.reply('MOTD removed.')

    @Plugin.command('help', parser=True)
    @Plugin.parser.add_argument('command', nargs='?')
    def on_help_command(self, event, args):
        """Get help."""
        if not args.command: # Display general help
            message = utils.create_general_help_message(
                is_user_admin=event.msg.author.id in app.config['DISCORD_BOT_ADMINS']
            )
        else: # Display command-specific help
            available_commands = constants.AVAILABLE_PUBLIC_COMMANDS_NAMES if event.msg.author.id not in app.config['DISCORD_BOT_ADMINS'] else constants.AVAILABLE_COMMANDS_NAMES

            if args.command not in available_commands:
                message = 'Invalid command name. Must be one of ' + ', '.join(available_commands)
            else:
                message = utils.create_command_help_message(args.command, constants.AVAILABLE_COMMANDS[args.command])

        event.msg.reply(message)

    @Plugin.command('info')
    def on_info_command(self, event):
        """Displays information about the bot."""
        info = [
            ':information_source: Hi! I was created by <@{}> around the beginning of March 2018.'.format(app.config['MY_DISCORD_ID']),
            'Like the RWRS website, my brain is powered by the Python programming language. More info: https://rwrstats.com/about',
            'P.S. You look beautiful today.'
        ]

        event.msg.reply('\n'.join(info))

    @Plugin.command('stats', parser=True)
    @Plugin.parser.add_argument('username')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    @Plugin.parser.add_argument('date', nargs='?')
    def on_stats_command(self, event, args):
        """Displays stats about a given player."""
        args.username = utils.prepare_username(args.username)

        if args.date: # Stats history lookup mode
            try:
                args.date = utils.parse_date(args.date)
            except Exception:
                event.msg.reply('Invalid date provided')

                return

            player_exist = rwr.scraper.search_player_by_username(args.database, args.username, check_exist_only=True)

            if not player_exist:
                event.msg.reply('Sorry dude, this player don\'t exist :confused:')

                return

            rwr_account = RwrAccount.get_by_type_and_username(args.database, args.username)

            if not rwr_account:
                event.msg.reply('Sorry my friend, stats history isn\'t recorded for this player :confused: He/she must be part of the {} {} most experienced players.'.format(
                    rwr.utils.get_database_name(args.database),
                    app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR'])
                )

                return

            rwr_account_stat = RwrAccountStat.get_stats_for_date(rwr_account.id, args.date)

            if not rwr_account_stat:
                event.msg.reply('No stats were found for the given date :confused: Are you sure he/she is part of the {} {} most experienced players?'.format(
                    rwr.utils.get_database_name(args.database),
                    app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR'])
                )

                return

            player = Player.craft(rwr_account, rwr_account_stat)
        else: # Live data mode
            player = rwr.scraper.search_player_by_username(args.database, args.username)

            if not player:
                event.msg.reply('Sorry dude, this player don\'t exist :confused:')

                return

        servers = rwr.scraper.get_servers()

        player.set_playing_on_server(servers)

        event.msg.reply('Here\'s stats for **{}** on **{}** ranked servers{}:'.format(
            player.username_display,
            player.database_name,
            ' for **' + args.date.format('MMMM D, YYYY') + '**' if args.date else ''
        ), embed=utils.create_player_message_embed(player))

    @Plugin.command('evolution', parser=True)
    @Plugin.parser.add_argument('username')
    @Plugin.parser.add_argument('type', choices=constants.VALID_EVOLUTION_TYPE_NAMES)
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_evolution_command(self, event, args):
        """Displays the evolution of the specified stat."""
        args.username = utils.prepare_username(args.username)

        player = rwr.scraper.search_player_by_username(args.database, args.username)

        if not player:
            event.msg.reply('Sorry dude, this player don\'t exist :confused:')

            return

        if not player.rwr_account:
            event.msg.reply('Sorry my friend, evolution is not available for this player :confused: He/she must be part of the {} {} most experienced players.'.format(
                rwr.utils.get_database_name(args.database),
                app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR'])
            )

            return

        evolution_chart = utils.create_evolution_chart(
            player.rwr_account.id,
            constants.VALID_EVOLUTION_TYPES[args.type]['column'],
            'Past year {} evolution for {}\n({} ranked servers, {} is better)'.format(
                constants.VALID_EVOLUTION_TYPES[args.type]['name'],
                player.username,
                player.database_name,
                'lower' if args.type == 'position' else 'higher'
            )
        )

        event.msg.reply('Here ya go:', attachments=[('evolution.png', evolution_chart, 'image/png')])

        evolution_chart.close()

    @Plugin.command('whereis', parser=True)
    @Plugin.parser.add_argument('username')
    def on_whereis_command(self, event, args):
        """Displays information about the server the given player is playing on."""
        args.username = utils.prepare_username(args.username)

        real_username, server = rwr.scraper.get_current_server_of_player(args.username)

        if not server:
            event.msg.reply('Nah, this player isn\'t currently playing online :disappointed:')

            return

        event.msg.reply('I found **{}** playing on **{}**:'.format(real_username, server.name), embed=utils.create_server_message_embed(server, username_to_highlight=real_username))

    @Plugin.command('server', parser=True)
    @Plugin.parser.add_argument('name')
    def on_server_command(self, event, args):
        """Displays information about the given server."""
        server = rwr.scraper.get_server_by_name(args.name)

        if not server:
            event.msg.reply('Sorry mate, I didn\'t find this server :disappointed:')

            return

        event.msg.reply('Here\'s information about **{}**:'.format(server.name), embed=utils.create_server_message_embed(server))

    @Plugin.command('now')
    def on_now_command(self, event):
        """Displays numbers about the current players and servers."""
        answer = [
            'There\'s currently **{total_players}** player{total_players_plural} in total. **{online_players}** of them {online_players_plural} playing multiplayer online.',
            'There\'s also **{total_servers}** online multiplayer servers, **{active_servers}** of which {active_servers_plural} active :wink:',
            '',
            'Talking about these numbers, here\'s some peaks:',
            '',
            '  - Total players peak: **{total_players_peak_count}** ({total_players_peak_date})',
            '  - Online players peak: **{online_players_peak_count}** ({online_players_peak_date})',
            '  - Online servers peak: **{online_servers_peak_count}** ({online_servers_peak_date})',
            '  - Active servers peak: **{active_servers_peak_count}** ({active_servers_peak_date})'
        ]

        total_players = self.steamworks_api_client.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])
        online_players, active_servers, total_servers = rwr.scraper.get_counters()

        peaks = Variable.get_peaks_for_display()

        event.msg.reply('\n'.join(answer).format(
            total_players=total_players,
            total_players_plural='s' if total_players > 1 else '',
            online_players=online_players,
            online_players_plural='are' if online_players > 1 else 'is',
            total_servers=total_servers,
            total_servers_plural='s' if total_servers > 1 else '',
            active_servers=active_servers,
            active_servers_plural='are' if active_servers > 1 else 'is',
            **peaks
        ))

    @Plugin.command('servers', parser=True)
    @Plugin.parser.add_argument('type', choices=constants.VALID_SERVER_TYPES.keys(), nargs='?', default=None)
    @Plugin.parser.add_argument('--ranked', action='store_const', const='yes')
    def on_servers_command(self, event, args):
        """Displays the first 10 currently active servers with room."""
        servers = rwr.scraper.filter_servers(
            limit=constants.SERVERS_LIMIT,
            not_empty='yes',
            not_full='yes',
            ranked=args.ranked,
            type=constants.VALID_SERVER_TYPES[args.type] if args.type else 'any'
        )

        if not servers:
            event.msg.reply('Well, looks like no servers are matching your request :disappointed:')

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
            response.append('{flag}`{current_players}/{max_players}` **{name}** ({type} • {map})\n{url}\n'.format(
                flag=':flag_' + server.location.country_code + ': ' if server.location.country_code else '',
                current_players=server.players.current,
                max_players=server.players.max,
                name=server.name_display,
                type=server.type_name,
                map=server.map.name_display,
                url=server.steam_join_link.replace(' ', '%20')
            ))

        event.msg.reply('\n'.join(response))

    @Plugin.command('top', parser=True)
    @Plugin.parser.add_argument('sort', choices=constants.VALID_PLAYER_SORTS.keys(), nargs='?', default='score')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_top_command(self, event, args):
        """Displays the top 24 players."""
        embed = utils.create_base_message_embed()

        players = rwr.scraper.get_players(
            args.database,
            limit=constants.PLAYERS_LIMIT,
            sort=constants.VALID_PLAYER_SORTS[args.sort]['value']
        )

        for player in players:
            embed.add_field(
                name='#{} {}'.format(player.leaderboard_position_display, player.username_display),
                value=constants.VALID_PLAYER_SORTS[args.sort]['getter'](player),
                inline=True
            )

        event.msg.reply('Everyone! The top {} **{}** players, ordered by {} :clap:'.format(
            constants.PLAYERS_LIMIT,
            rwr.utils.get_database_name(args.database),
            constants.VALID_PLAYER_SORTS[args.sort]['name']
        ), embed=embed)

    @Plugin.command('pos', parser=True)
    @Plugin.parser.add_argument('username')
    @Plugin.parser.add_argument('sort', choices=constants.VALID_PLAYER_SORTS.keys(), nargs='?', default='score')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    def on_pos_command(self, event, args):
        """Highlights the given player in the leaderboard."""
        args.username = utils.prepare_username(args.username)

        players = rwr.scraper.get_players(
            args.database,
            limit=constants.PLAYERS_LIMIT,
            target=args.username,
            sort=constants.VALID_PLAYER_SORTS[args.sort]['value']
        )

        if not players:
            event.msg.reply('Sorry dude, this player don\'t exist :confused:')

            return

        embed = utils.create_base_message_embed()

        username = args.username

        for player in players:
            if player.username == args.username:
                username = player.username_display

            embed.add_field(
                name='{}#{} {}'.format('➡️ ' if player.username == args.username else '', player.leaderboard_position, player.username_display),
                value=constants.VALID_PLAYER_SORTS[args.sort]['getter'](player),
                inline=True
            )

        event.msg.reply('Here\'s the position of **{}** on the **{}** leaderboard, ordered by {}:'.format(
            username,
            rwr.utils.get_database_name(args.database),
            constants.VALID_PLAYER_SORTS[args.sort]['name']
        ), embed=embed)

    @Plugin.command('compare', parser=True)
    @Plugin.parser.add_argument('source_username')
    @Plugin.parser.add_argument('target_username')
    @Plugin.parser.add_argument('database', choices=rwr.constants.VALID_DATABASES, nargs='?', default='invasion')
    @Plugin.parser.add_argument('date', nargs='?')
    def on_compare_command(self, event, args):
        """Compare stats of two players."""
        args.source_username = utils.prepare_username(args.source_username)
        args.target_username = utils.prepare_username(args.target_username)

        if args.date: # Stats history lookup mode
            try:
                args.date = utils.parse_date(args.date)
            except Exception:
                event.msg.reply('Invalid date provided')

                return

            source_player_exist = rwr.scraper.search_player_by_username(args.database, args.source_username, check_exist_only=True)

            if not source_player_exist:
                event.msg.reply('I\'m sorry, I cannot find **{}** :confused:'.format(args.source_username))

                return

            source_rwr_account = RwrAccount.get_by_type_and_username(args.database, args.source_username)

            if not source_rwr_account:
                event.msg.reply('Sorry my friend, stats history isn\'t recorded for {} :confused: He/she must be part of the {} {} most experienced players.'.format(
                    args.source_username,
                    rwr.utils.get_database_name(args.database),
                    app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR'])
                )

                return

            source_rwr_account_stat = RwrAccountStat.get_stats_for_date(source_rwr_account.id, args.date)

            if not source_rwr_account_stat:
                event.msg.reply('No stats were found for the given date for {} :confused: Are you sure he/she is/was part of the {} {} most experienced players?'.format(
                    args.source_username,
                    rwr.utils.get_database_name(args.database),
                    app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR'])
                )

                return

            source_player = Player.craft(source_rwr_account, source_rwr_account_stat)

            target_player_exist = rwr.scraper.search_player_by_username(args.database, args.target_username, check_exist_only=True)

            if not target_player_exist:
                event.msg.reply('I\'m sorry, I cannot find **{}** :confused:'.format(args.target_username))

                return

            target_rwr_account = RwrAccount.get_by_type_and_username(args.database, args.target_username)

            if not target_rwr_account:
                event.msg.reply('Sorry my friend, stats history isn\'t recorded for {} :confused: He/she must be part of the {} {} most experienced players.'.format(
                    args.target_username,
                    rwr.utils.get_database_name(args.database),
                    app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR'])
                )

                return

            target_rwr_account_stat = RwrAccountStat.get_stats_for_date(target_rwr_account.id, args.date)

            if not target_rwr_account_stat:
                event.msg.reply('No stats were found for the given date for {} :confused: Are you sure he/she is/was part of the {} {} most experienced players?'.format(
                    args.target_username,
                    rwr.utils.get_database_name(args.database),
                    app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR'])
                )

                return

            target_player = Player.craft(target_rwr_account, target_rwr_account_stat)
        else: # Live data mode
            source_player = rwr.scraper.search_player_by_username(args.database, args.source_username)

            if not source_player:
                event.msg.reply('I\'m sorry, I cannot find **{}** :confused:'.format(args.source_username))

                return

            target_player = rwr.scraper.search_player_by_username(args.database, args.target_username)

            if not target_player:
                event.msg.reply('Nah, I cannot find **{}** :confused:'.format(args.target_username))

                return

        table_data = [
            [
                'Rank',
                source_player.rank.name + '\n(' + source_player.rank.alternative_name + ')' if source_player.rank.alternative_name else source_player.rank.name,
                utils.compare_values(source_player, target_player, lambda player: player.rank.id),
                target_player.rank.name + '\n(' + target_player.rank.alternative_name + ')' if target_player.rank.alternative_name else target_player.rank.name
            ],
            ['XP', source_player.xp_display, utils.compare_values(source_player, target_player, lambda player: player.xp), target_player.xp_display],
            ['Kills', source_player.kills_display, utils.compare_values(source_player, target_player, lambda player: player.kills), target_player.kills_display],
            ['Deaths', source_player.deaths_display, utils.compare_values(source_player, target_player, lambda player: player.deaths), target_player.deaths_display],
            ['K/D ratio', source_player.kd_ratio, utils.compare_values(source_player, target_player, lambda player: player.kd_ratio), target_player.kd_ratio],
            ['Score', source_player.score_display, utils.compare_values(source_player, target_player, lambda player: player.score), target_player.score_display],
            ['Time played', helpers.humanize_seconds_to_hours(source_player.time_played), utils.compare_values(source_player, target_player, lambda player: player.time_played), helpers.humanize_seconds_to_hours(target_player.time_played)],
            ['Kill streak', source_player.longest_kill_streak_display, utils.compare_values(source_player, target_player, lambda player: player.longest_kill_streak), target_player.longest_kill_streak_display],
            ['Teamkills', source_player.teamkills_display, utils.compare_values(source_player, target_player, lambda player: player.teamkills), target_player.teamkills_display],
            ['Heals', source_player.soldiers_healed_display, utils.compare_values(source_player, target_player, lambda player: player.soldiers_healed), target_player.soldiers_healed_display],
            ['Shots fired', source_player.shots_fired_display, utils.compare_values(source_player, target_player, lambda player: player.shots_fired), target_player.shots_fired_display],
            ['Distance moved', '{}km'.format(source_player.distance_moved), utils.compare_values(source_player, target_player, lambda player: player.distance_moved), '{}km'.format(target_player.distance_moved)],
            ['Throwables thrown', source_player.throwables_thrown_display, utils.compare_values(source_player, target_player, lambda player: player.throwables_thrown), target_player.throwables_thrown_display],
            ['Vehicles destroyed', source_player.vehicles_destroyed_display, utils.compare_values(source_player, target_player, lambda player: player.vehicles_destroyed), target_player.vehicles_destroyed_display],
            ['Targets destroyed', source_player.targets_destroyed_display, utils.compare_values(source_player, target_player, lambda player: player.targets_destroyed), target_player.targets_destroyed_display]
        ]

        table_headers = ['', source_player.username, 'vs', target_player.username]

        table = tabulate(table_data, headers=table_headers, tablefmt='presto')

        event.msg.reply('Who {} the biggest between **{}** and **{}** on the **{}** leaderboard{}?\n```\n{}\n```'.format(
            'had' if args.date else 'has',
            source_player.username_display,
            target_player.username_display,
            rwr.utils.get_database_name(args.database),
            ' for **' + args.date.format('MMMM D, YYYY') + '**' if args.date else '',
            table
        ))


class RwrsBot:
    """The high-level class that wraps the RWRS Discord bot logic."""
    def __init__(self):
        setup_logging(level=logging.WARNING)

        self.client_config = ClientConfig()
        self.client_config.token = app.config['DISCORD_BOT_TOKEN']

        self.client = Client(self.client_config)

        self.bot_config = BotConfig()
        self.bot_config.http_enabled = True

        self.bot = Bot(self.client, config=self.bot_config)
        self.bot.add_plugin(RwrsBotDiscoPlugin)

    def run(self):
        """Actually run the RWRS Discord bot."""
        self.bot.run_forever()
