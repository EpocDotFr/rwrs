from flask_discord_interactions import Message, Permission
from rwrs import discord_interactions, cache, db
from models import Variable, User
from . import constants
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
    return Message('TODO', ephemeral=True)


@event_command_group.command(
    'remove',
    'Removes next RWR event'
)
def event_remove(
    ctx
):
    return Message('TODO', ephemeral=True)


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
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE,
    date: str = None
):
    return 'TODO'


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
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE
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
    return 'TODO'


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
    return 'TODO'


@discord_interactions.command(
    'now',
    'Displays numbers about the current players and servers'
)
def now(
    ctx
):
    return 'TODO'


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
    return 'TODO'


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
    sort: constants.PLAYER_SORT_CHOICES = constants.DEFAULT_PLAYER_SORT,
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE
):
    return 'TODO'


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
    sort: constants.PLAYER_SORT_CHOICES = constants.DEFAULT_PLAYER_SORT,
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE
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
    database: constants.DATABASE_CHOICES = constants.DEFAULT_DATABASE,
    date: str = None
):
    return 'TODO'
