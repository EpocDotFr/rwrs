from flask_discord_interactions import Channel
from rwrs import discord_interactions

maintenance_command_group = discord_interactions.command_group('maintenance')
motd_command_group = discord_interactions.command_group('motd')
user_command_group = discord_interactions.command_group('user')
event_command_group = discord_interactions.command_group('event')


@discord_interactions.command('cc', 'Clears the RWRS cache')
def cc(ctx):
    return 'TODO'


@discord_interactions.command('say', 'Makes the bot to say something', annotations={'channel': 'The channel in which the message should be sent', 'message': 'The message to send'})
def say(ctx, channel: Channel, message: str):
    return 'TODO'


@maintenance_command_group.command('enable', 'Enables the maintenance mode')
def maintenance_enable(ctx):
    return 'TODO'


@maintenance_command_group.command('disable', 'Disables the maintenance mode')
def maintenance_disable(ctx):
    return 'TODO'


@motd_command_group.command('set', 'Sets the MOTD', annotations={'message': 'Content of the MOTD. Markdown is supported'})
def motd_set(ctx, message: str):
    return 'TODO'


@motd_command_group.command('remove', 'Removes the MOTD')
def motd_remove(ctx):
    return 'TODO'


@user_command_group.command('api-ban', 'Ban a user from using the API', annotations={'user_id': 'A RWRS user ID'})
def user_api_ban(ctx, user_id: int):
    return 'TODO'


@user_command_group.command('api-unban', 'Unban a user from using the API', annotations={'user_id': 'A RWRS user ID'})
def user_api_unban(ctx, user_id: int):
    return 'TODO'


@event_command_group.command('set', 'Sets the next RWR event', annotations={'name': 'Name of the event', 'datetime': 'Date and time when the event will begin. Format: YYYY-MM-DD HH:mm ZZZ', 'server_ip_and_port': 'The server IP and port where the event will take place. Format: {ip}:{port}'})
def event_set(ctx, name: str, datetime: str, server_ip_and_port: str = None):
    return 'TODO'


@event_command_group.command('remove', 'Removes the next RWR event')
def event_remove(ctx):
    return 'TODO'
