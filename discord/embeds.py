from flask_discord_interactions.models.embed import Media, Field, Footer
from flask_discord_interactions.models import Embed
from . import constants
from rwrs import app
import helpers


def create_player_message_embed(player, description_addendum=None):
    """Create a RWRS player rich Discord message."""
    embed = create_base_message_embed()

    embed.url = player.link_absolute

    description = []

    if player.is_myself:
        description.append(':wave: Hey, I\'m the creator of RWRS and this bot! Glad to see you\'re using it.')
    elif player.is_contributor:
        description.append(':v: This player contributed in a way or another to RWRS. Thanks to her/him!')
    elif player.is_rwr_dev:
        description.append(':hammer_and_wrench: Say hi to one of the Running With Rifles developers!')

    if player.is_ranked_servers_mod:
        description.append(':scales: Ranked (official) servers moderator')

    if description_addendum:
        description.append(description_addendum)

    if description:
        embed.description = '\n'.join(description)

    embed.thumbnail = Media(player.rank.image_absolute)

    embed.fields = []

    embed.fields.append(Field(
        'Current rank',
        '{}\n{}{} XP'.format(
            player.rank.name,
            '(' + player.rank.alternative_name + ')\n' if player.rank.alternative_name else '',
            player.xp_display
        ),
        inline=True
    ))

    embed.fields.append(Field(
        'Next rank',
        '{}\n{}{} XP'.format(
            player.next_rank.name,
            '(' + player.next_rank.alternative_name + ')\n' if player.next_rank.alternative_name else '',
            helpers.humanize_integer(player.next_rank.xp)
        ) if player.next_rank else 'Highest possible\nrank reached',
        inline=True
    ))

    if player.next_rank:
        embed.fields.append(Field(
            'Next rank progression',
            '{}% - {} XP remaining'.format(
                player.xp_percent_completion_to_next_rank,
                helpers.humanize_integer(player.xp_to_next_rank)
            )
        ))

    embed.fields.append(Field(
        'Kills',
        player.kills_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Deaths',
        player.deaths_display,
        inline=True
    ))

    embed.fields.append(Field(
        'K/D ratio',
        str(player.kd_ratio),
        inline=True
    ))

    embed.fields.append(Field(
        'Score',
        player.score_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Time played',
        helpers.humanize_seconds_to_hours(player.time_played) + ' (' + helpers.humanize_seconds_to_days(player.time_played) + ')' if player.display_time_played_in_days else helpers.humanize_seconds_to_hours(player.time_played),
        inline=True
    ))

    embed.fields.append(Field(
        'Kill streak',
        player.longest_kill_streak_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Teamkills',
        player.teamkills_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Heals',
        player.soldiers_healed_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Shots fired',
        player.shots_fired_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Distance moved',
        '{}km'.format(player.distance_moved),
        inline=True
    ))

    embed.fields.append(Field(
        'Throwables thrown',
        player.throwables_thrown_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Vehicles destroyed',
        player.vehicles_destroyed_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Targets destroyed',
        player.targets_destroyed_display,
        inline=True
    ))

    if player.playing_on_server:
        embed.footer = Footer('🖱 Playing on {} ({})'.format(
            player.playing_on_server.name_display,
            player.playing_on_server.summary
        ))

    return embed


def create_server_message_embed(server, username_to_highlight=None, advertise_event=True):
    """Create a RWRS server rich Discord message."""
    embed = create_base_message_embed()

    embed.url = server.link_absolute

    description = [server.steam_join_link.replace(' ', '%20')]

    if advertise_event and server.event:
        description.append(':calendar: {} event on this server: **{}**{}'.format(
            'Ongoing' if server.event['is_ongoing'] else 'Upcoming',
            server.event['name'],
            ' - ' + server.event['datetime'].format(app.config['EVENT_DATETIME_DISPLAY_FORMAT']) if not server.event['is_ongoing'] else ''
        ))

    embed.description = '\n'.join(description)

    embed.fields = []

    if server.players.list:
        if not username_to_highlight:
            players_list = server.players.list
        else:
            players_list = ['**{}**'.format(username) if username == username_to_highlight else username for username in server.players.list]

        embed.fields.append(Field(
            'Players list',
            ', '.join(players_list)
        ))

    if server.map.has_preview:
        embed.image = Media(server.map.preview_absolute)
    elif server.map.has_minimap:
        embed.image = Media(server.map.minimap_absolute)

    embed.fields.append(Field(
        'Players count',
        '{}/{}'.format(server.players.current, server.players.max),
        inline=True
    ))

    embed.fields.append(Field(
        'Map',
        server.map.name_display,
        inline=True
    ))

    embed.fields.append(Field(
        'Type',
        server.type_name,
        inline=True
    ))

    embed.fields.append(Field(
        'Mode',
        server.mode_name,
        inline=True
    ))

    if server.location.country_code:
        embed.fields.append(Field(
            'Location',
            ':flag_{}: {}'.format(
                server.location.country_code,
                server.location.text
            ),
            inline=True
        ))

    if server.is_ranked:
        embed.footer = Footer('⭐️ Ranked {} server'.format(server.database_name))

    return embed


def create_base_message_embed():
    """Create a base rich Discord message."""
    return Embed(
        color=constants.EMBED_COLOR
    )
