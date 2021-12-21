from flask_discord_interactions.embed import Media, Field, Footer
from flask_discord_interactions import Embed
from . import constants
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

    embed.fields.append(Field(
        name='Current rank',
        value='{}\n{}{} XP'.format(
            player.rank.name,
            '(' + player.rank.alternative_name + ')\n' if player.rank.alternative_name else '',
            player.xp_display
        ),
        inline=True
    ))

    embed.fields.append(Field(
        name='Next rank',
        value='{}\n{}{} XP'.format(
            player.next_rank.name,
            '(' + player.next_rank.alternative_name + ')\n' if player.next_rank.alternative_name else '',
            helpers.humanize_integer(player.next_rank.xp)
        ) if player.next_rank else 'Highest possible\nrank reached',
        inline=True
    ))

    if player.next_rank:
        embed.fields.append(Field(
            name='Next rank progression',
            value='{}% - {} XP remaining'.format(
                player.xp_percent_completion_to_next_rank,
                helpers.humanize_integer(player.xp_to_next_rank)
            )
        ))

    embed.fields.append(Field(
        name='Kills',
        value=player.kills_display,
        inline=True
    ))

    embed.fields.append(Field(
        name='Deaths',
        value=player.deaths_display,
        inline=True
    ))

    embed.fields.append(Field(
        name='K/D ratio',
        value=player.kd_ratio,
        inline=True
    ))

    embed.fields.append(Field(
        name='Score',
        value=player.score_display,
        inline=True
    ))

    embed.fields.append(Field(
        name='Time played',
        value=helpers.humanize_seconds_to_hours(player.time_played) + ' (' + helpers.humanize_seconds_to_days(player.time_played) + ')' if player.display_time_played_in_days else helpers.humanize_seconds_to_hours(player.time_played),
        inline=True
    ))

    embed.fields.append(Field(
        name='Kill streak',
        value=player.longest_kill_streak_display,
        inline=True
    ))

    embed.fields.append(Field(
        name='Teamkills',
        value=player.teamkills_display,
        inline=True
    ))

    embed.fields.append(
        name='Heals',
        value=player.soldiers_healed_display,
        inline=True
    )

    embed.fields.append(Field(
        name='Shots fired',
        value=player.shots_fired_display,
        inline=True
    ))

    embed.fields.append(Field(
        name='Distance moved',
        value='{}km'.format(player.distance_moved),
        inline=True
    ))

    embed.fields.append(Field(
        name='Throwables thrown',
        value=player.throwables_thrown_display,
        inline=True
    ))

    embed.fields.append(Field(
        name='Vehicles destroyed',
        value=player.vehicles_destroyed_display,
        inline=True
    ))

    embed.fields.append(Field(
        name='Targets destroyed',
        value=player.targets_destroyed_display,
        inline=True
    ))

    if player.playing_on_server:
        embed.footer = Footer(text='🖱 Playing on {} ({})'.format(
            player.playing_on_server.name_display,
            player.playing_on_server.summary
        ))

    return embed


def create_base_message_embed():
    """Create a rich Discord message."""
    embed = Embed()

    embed.color = constants.EMBED_COLOR

    return embed
