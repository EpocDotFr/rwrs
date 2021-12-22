from models import Variable, User, RwrAccount, RwrAccountStat
from flask_discord_interactions.models.embed import Field
from flask_discord_interactions import Message, Permission
from rwrs import app, cache, db, discord_interactions
from . import constants, utils, embeds
from rwr.player import Player
import steam_helpers
import rwr.scraper
import arrow
import os

maintenance_command_group = discord_interactions.command_group('maintenance')
motd_command_group = discord_interactions.command_group('motd')
user_command_group = discord_interactions.command_group('user')
user_api_command_subgroup = user_command_group.subgroup('api')
event_command_group = discord_interactions.command_group('event')


@discord_interactions.command(
    'cc',
    'Clears RWRS cache',
    default_permission=False,
    permissions=[
        Permission(user=constants.MY_DISCORD_ID)
    ]
)
def cc(
    ctx
):
    cache.clear()

    return Message('Cache cleared.', ephemeral=True)


@maintenance_command_group.command(
    'enable',
    'Enables maintenance mode'
)
def maintenance_enable(
    ctx
):
    if os.path.exists('maintenance'):
        return Message('Maintenance mode already enabled.', ephemeral=True)
    else:
        open('maintenance', 'a').close()

        return Message('Maintenance mode enabled.', ephemeral=True)


@maintenance_command_group.command(
    'disable',
    'Disables maintenance mode'
)
def maintenance_disable(
    ctx
):
    if not os.path.exists('maintenance'):
        return Message('Maintenance mode already disabled.', ephemeral=True)
    else:
        os.remove('maintenance')

        return Message('Maintenance mode disabled.', ephemeral=True)


@motd_command_group.command(
    'set',
    'Sets MOTD',
    annotations={
        'message': 'Markdown is supported'
    }
)
def motd_set(
    ctx,
    message: str
):
    Variable.set_value('motd', message)

    db.session.commit()

    return Message('MOTD updated.', ephemeral=True)


@motd_command_group.command(
    'remove',
    'Removes MOTD'
)
def motd_remove(
    ctx
):
    if not Variable.get_value('motd'):
        return Message('MOTD already removed.', ephemeral=True)
    else:
        Variable.set_value('motd', None)

        db.session.commit()

        return Message('MOTD removed.', ephemeral=True)


@user_api_command_subgroup.command(
    'ban',
    'Ban a user from using the API',
    annotations={
        'user_id': 'An RWRS user ID'
    }
)
def user_api_ban(
    ctx,
    user_id: int
):
    user = User.query.get(user_id)

    if not user:
        return Message('User not found.', ephemeral=True)
    elif user.is_forbidden_to_access_api:
        return Message('{} is already banned from using the API.'.format(user.username), ephemeral=True)
    else:
        try:
            user.is_forbidden_to_access_api = True

            db.session.add(user)
            db.session.commit()

            return Message('{} has been successfully banned from using the API.'.format(user.username), ephemeral=True)
        except Exception as e:
            return Message('Error banning {}: {}'.format(user.username, e), ephemeral=True)


@user_api_command_subgroup.command(
    'unban',
    'Unban a user from using the API',
    annotations={
        'user_id': 'An RWRS user ID'
    }
)
def user_api_unban(
    ctx,
    user_id: int
):
    user = User.query.get(user_id)

    if not user:
        return Message('User not found.', ephemeral=True)
    elif not user.is_forbidden_to_access_api:
        return Message('{} is already able to use the API.'.format(user.username), ephemeral=True)
    else:
        try:
            user.is_forbidden_to_access_api = False

            db.session.add(user)
            db.session.commit()

            return Message('{} is now able to use the API.'.format(user.username), ephemeral=True)
        except Exception as e:
            return Message('Error unbanning {}: {}'.format(user.username, e), ephemeral=True)


@event_command_group.command(
    'set',
    'Sets next RWR event',
    annotations={
        'datetime': 'Format: YYYY-MM-DD HH:mm ZZZ',
        'server_ip_and_port': 'Format: {ip}:{port}'
    }
)
def event_set(
    ctx,
    name: str,
    datetime: str,
    server_ip_and_port: str = None
):
    try:
        Variable.set_event(name, datetime, server_ip_and_port)

        db.session.commit()

        cache.delete_memoized(rwr.scraper.get_servers)

        return Message('Event updated.', ephemeral=True)
    except (arrow.parser.ParserError, ValueError):
        return Message('Invalid datetime provided (should be `{}`)'.format(app.config['EVENT_DATETIME_STORAGE_FORMAT']), ephemeral=True)


@event_command_group.command(
    'remove',
    'Removes next RWR event'
)
def event_remove(
    ctx
):
    if not Variable.get_value('event'):
        return Message('Event already removed.', ephemeral=True)
    else:
        Variable.set_value('event', None)

        db.session.commit()

        cache.delete_memoized(rwr.scraper.get_servers)

        return Message('Event removed.', ephemeral=True)


@discord_interactions.command(
    'info',
    'Displays information about the bot'
)
def info(
    ctx
):
    return '\n'.join([
        ':information_source: Hi! I was created by <@{}> around the beginning of March 2018.'.format(constants.MY_DISCORD_ID),
        'Like the RWRS website, my brain is powered by the Python programming language. More info: https://rwrstats.com/about',
        'P.S. You look beautiful today.'
    ])


@discord_interactions.command(
    'stats',
    'Displays stats about a given player',
    annotations={
        'username': 'A full RWR username',
        'database': 'Official (ranked) server type to get data from (defaults to {})'.format(constants.DEFAULT_DATABASE.value),
        'date': 'Get stats for given date (defaults to current)'
    }
)
def stats(
    ctx,
    username: str,
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE.value,
    date: str = None
):
    username = utils.prepare_username(username)

    if date: # Stats history lookup mode
        try:
            date = utils.parse_date(date)
        except Exception:
            return Message(
                '\n'.join([
                    'Invalid date provided. Allowed values / formats:',
                    '  - `yesterday`',
                    '  - `1 day ago` / `{{number}} days ago`',
                    '  - `1 week ago` / `{{number}} weeks ago`',
                    '  - `1 month ago` / `{{number}} months ago`',
                    '  - `1 year ago` / `{{number}} years ago`',
                    '  - `{{month name}} {{day number}}`',
                    '  - `{{month name}} {{day number}} {{year}}`',
                    '  - `{{month name}} {{day number}}, {{year}}`',
                    '  - `{{year}}-{{month number}}-{{day number}}`',
                    '  - `{{day number}}/{{month number}}/{{year}}`',
                ]),
                ephemeral=True
            )

        player_exist = rwr.scraper.search_player_by_username(database, username, check_exist_only=True)

        if not player_exist:
            return 'Sorry dude, this player don\'t exist :confused:'

        rwr_account = RwrAccount.get_by_type_and_username(database, username)

        if not rwr_account:
            return 'Sorry my friend, stats history isn\'t recorded for this player :confused: He/she must be part of the {} {} most experienced players.'.format(
                rwr.utils.get_database_name(database),
                app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']
            )

        rwr_account_stat = RwrAccountStat.get_stats_for_date(rwr_account.id, date)

        if not rwr_account_stat:
            return 'No stats were found for the given date :confused: Are you sure he/she is part of the {} {} most experienced players?'.format(
                rwr.utils.get_database_name(database),
                app.config['MAX_NUM_OF_PLAYERS_TO_TRACK_STATS_FOR']
            )

        rwr_account_stat.rwr_account = rwr_account # Setting the RwrAccount relation now to prevent lazy loading issue (also preventing one extra DB query)

        player = Player.craft(rwr_account, rwr_account_stat)

        description_addendum = ':up: Promoted that day to ' + rwr_account_stat.promoted_to_rank.name_display if rwr_account_stat.promoted_to_rank else None
    else: # Live data mode
        player = rwr.scraper.search_player_by_username(database, username)

        if not player:
            return 'Sorry dude, this player don\'t exist :confused:'

        description_addendum = None

    servers = rwr.scraper.get_servers()

    player.set_playing_on_server(servers)

    return Message(
        'Here\'s stats for **{}** on **{}** ranked servers{}:'.format(
            player.username_display,
            player.database_name,
            ' for **' + date.format('MMMM D, YYYY') + '**' if date else ''
        ),
        embed=embeds.create_player_message_embed(player, description_addendum=description_addendum)
    )


@discord_interactions.command(
    'evolution',
    'Displays evolution of specified stat',
    annotations={
        'username': 'A full RWR username',
        'database': 'Official (ranked) server type to get data from (defaults to {})'.format(constants.DEFAULT_DATABASE.value)
    }
)
def evolution(
    ctx,
    username: str,
    type: constants.EVOLUTION_TYPE_CHOICES,
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE.value
):
    return 'TODO'


@discord_interactions.command(
    'whereis',
    'Displays information about the server the given player is playing on',
    annotations={
        'username': 'A RWR username (may be partial)'
    }
)
def whereis(
    ctx,
    username: str
):
    username = utils.prepare_username(username)

    real_username, server = rwr.scraper.get_current_server_of_player(username)

    if not server:
        return 'Nah, this player isn\'t currently playing online :disappointed:'

    return Message(
        'I found **{}** playing on **{}**:'.format(real_username, server.name),
        embed=embeds.create_server_message_embed(server, username_to_highlight=real_username)
    )


@discord_interactions.command(
    'server',
    'Displays information about the given server',
    annotations={
        'username': 'A server name (may be partial)'
    }
)
def server(
    ctx,
    name: str
):
    server = rwr.scraper.get_server_by_name(name)

    if not server:
        return 'Sorry mate, I didn\'t find this server :disappointed:'

    return Message(
        'Here\'s information about **{}**:'.format(server.name),
        embed=embeds.create_server_message_embed(server)
    )


@discord_interactions.command(
    'now',
    'Displays numbers about the current players and servers'
)
def now(
    ctx
):
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

    total_players = steam_helpers.get_current_players_count_for_app(app.config['RWR_STEAM_APP_ID'])
    online_players, active_servers, total_servers = rwr.scraper.get_counters()

    peaks = Variable.get_peaks_for_display()

    return '\n'.join(answer).format(
        total_players=total_players,
        total_players_plural='s' if total_players > 1 else '',
        online_players=online_players,
        online_players_plural='are' if online_players > 1 else 'is',
        total_servers=total_servers,
        total_servers_plural='s' if total_servers > 1 else '',
        active_servers=active_servers,
        active_servers_plural='are' if active_servers > 1 else 'is',
        **peaks
    )


@discord_interactions.command(
    'servers',
    'Displays first {} currently active servers with room'.format(constants.SERVERS_LIMIT),
    annotations={
        'ranked_only': 'Only return ranked (official) servers'
    }
)
def servers(
    ctx,
    type: constants.SERVER_TYPE_CHOICES = None,
    ranked_only: bool = False
):
    servers = rwr.scraper.filter_servers(
        limit=constants.SERVERS_LIMIT,
        not_empty='yes',
        not_full='yes',
        ranked='yes' if ranked_only else None,
        type=type if type else 'any'
    )

    if not servers:
        return 'Well, looks like no servers are matching your request :disappointed:'

    filters = []

    if ranked_only:
        filters.append('ranked')

    if type:
        filters.append(rwr.constants.SERVER_TYPES[type])

    filters_string = ', ' + ', '.join(filters) if filters else ''

    response = [
        'Here, the first {} currently active{} servers with room:\n'.format(constants.SERVERS_LIMIT, filters_string)
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

    return '\n'.join(response)


@discord_interactions.command(
    'top',
    'Displays the top {} players'.format(constants.PLAYERS_LIMIT),
    annotations={
        'sort': 'Defaults to {}'.format(constants.DEFAULT_PLAYER_SORT.value),
        'database': 'Official (ranked) server type to get data from (defaults to {})'.format(constants.DEFAULT_DATABASE.value)
    }
)
def top(
    ctx,
    sort: constants.PLAYER_SORT_CHOICES = constants.DEFAULT_PLAYER_SORT.value,
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE.value
):
    embed = embeds.create_base_message_embed()

    embed.fields = []

    players = rwr.scraper.get_players(
        database,
        limit=constants.PLAYERS_LIMIT,
        sort=constants.PLAYER_SORTS[sort]['value']
    )

    for player in players:
        embed.fields.append(Field(
            '#{} {}'.format(player.leaderboard_position_display, player.username_display),
            constants.PLAYER_SORTS[sort]['getter'](player),
            inline=True
        ))

    return Message(
        'Everyone! The top {} **{}** players, ordered by {} :clap:'.format(
            constants.PLAYERS_LIMIT,
            rwr.utils.get_database_name(database),
            constants.PLAYER_SORTS[sort]['name']
        ),
        embed=embed
    )


@discord_interactions.command(
    'pos',
    'Highlights the given player in the leaderboard',
    annotations={
        'username': 'A full RWR username',
        'sort': 'Defaults to {}'.format(constants.DEFAULT_PLAYER_SORT.value),
        'database': 'Official (ranked) server type to get data from (defaults to {})'.format(constants.DEFAULT_DATABASE.value)
    }
)
def pos(
    ctx,
    username: str,
    sort: constants.PLAYER_SORT_CHOICES = constants.DEFAULT_PLAYER_SORT.value,
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE.value
):
    return 'TODO'


@discord_interactions.command(
    'compare',
    'Compare stats between two players',
    annotations={
        'source_username': 'A full RWR username',
        'target_username': 'A full RWR username',
        'database': 'Official (ranked) server type to get data from (defaults to {})'.format(constants.DEFAULT_DATABASE.value),
        'date': 'Get stats for given date (defaults to current)'
    }
)
def compare(
    ctx,
    source_username: str,
    target_username: str,
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE.value,
    date: str = None
):
    return 'TODO'
