from disco.types.message import MessageEmbed
from . import constants
import helpers


def create_player_message_embed(player):
    """Create a RWRS player rich Discord message."""
    embed = create_base_message_embed()

    embed.url = player.link_absolute

    if player.is_me:
        embed.description = ':wave: Hey, I\'m the creator of RWRS and this bot! Glad to see you\'re using it.'
    elif player.is_contributor:
        embed.description = ':v: This player contributed in a way or another to RWRS. Thanks to her/him!'
    elif player.is_rwr_dev:
        embed.description = ':hammer_and_wrench: Say hi to one of the Running With Rifles developers!'

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

    embed.add_field(
        name='Kill streak',
        value=player.longest_kill_streak_display,
        inline=True
    )

    embed.add_field(
        name='Teamkills',
        value=player.teamkills_display,
        inline=True
    )

    embed.add_field(
        name='Heals',
        value=player.soldiers_healed_display,
        inline=True
    )

    embed.add_field(
        name='Shots fired',
        value=player.shots_fired_display,
        inline=True
    )

    embed.add_field(
        name='Distance moved',
        value='{}km'.format(player.distance_moved),
        inline=True
    )

    embed.add_field(
        name='Throwables thrown',
        value=player.throwables_thrown_display,
        inline=True
    )

    embed.add_field(
        name='Vehicles destroyed',
        value=player.vehicles_destroyed_display,
        inline=True
    )

    embed.add_field(
        name='Targets destroyed',
        value=player.targets_destroyed_display,
        inline=True
    )

    if player.playing_on_server:
        embed.set_footer(text='🖱 Playing on {} ({})'.format(
            player.playing_on_server.name_display,
            player.playing_on_server.summary
        ))

    return embed


def create_server_message_embed(server, username_to_highlight=None):
    """Create a RWRS server rich Discord message."""
    embed = create_base_message_embed()

    embed.url = server.link_absolute
    embed.description = server.steam_join_link.replace(' ', '%20')

    if server.players.list:
        if not username_to_highlight:
            players_list = server.players.list
        else:
            players_list = ['**{}**'.format(username) if username == username_to_highlight else username for username in server.players.list]

        embed.add_field(
            name='Players list',
            value=', '.join(players_list)
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


def create_base_message_embed():
    """Create a rich Discord message."""
    embed = MessageEmbed()

    embed.color = constants.EMBED_COLOR

    return embed


def compare_values(source_player, target_player, getter):
    """Create the comparison cell for the compare command."""
    source_value = getter(source_player)
    target_value = getter(target_player)

    def _compare(source_value, target_value):
        if source_value > target_value:
            return '▲'
        elif source_value < target_value:
            return '▼'
        else:
            return '='

    return _compare(source_value, target_value) + '  ' + _compare(target_value, source_value)


def prepare_username(username):
    """Perform some action to a RWR username to be ready to be consumed by the bot."""
    username = username.upper()

    if not username.startswith('\-'):
        return username

    return username.replace('\-', '-', 1)


def create_general_help_message(is_user_admin=False):
    """Create the general help message with the available commands list."""
    with open('docs/discord_bot/general.md', 'r', encoding='utf-8') as f:
        message = f.read()

    message += '\n\n**:page_facing_up: Commands list**\n\n'

    commands_help = []

    for name, info in constants.AVAILABLE_COMMANDS.items():
        if not is_user_admin and info['admin_only']:
            continue

        commands_help.append('- `{}`: {}'.format(name, info['description']))

    message += '\n'.join(commands_help)
    message += '\n\nType `@rwrs help {command name}` for help regarding a specific command.'

    return message
