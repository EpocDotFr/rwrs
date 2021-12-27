from flask_discord_interactions import ActionRow, Button, ButtonStyles
from flask import url_for


def create_player_components(player, tab=None):
    params = {
        'database': player.database,
        'username': player.username,
    }

    if tab:
        params['tab'] = tab

    return create_single_button_with_link_component(
        url_for('player_details', **params, _external=True)
    )


def create_players_components(database, sort=None, target=None):
    params = {
        'database': database,
    }

    if sort:
        params['sort'] = sort

    if target:
        params['target'] = target

    return create_single_button_with_link_component(
        url_for('players_list', **params, _external=True),
        label='Full list on rwrstats.com'
    )


def create_players_comparison_components(database, source_player, target_player):
    return create_single_button_with_link_component(
        url_for(
            'players_compare',
            database=database,
            username=source_player.username,
            username_to_compare_with=target_player.username,
            _external=True
        )
    )


def create_server_components(server):
    return create_single_button_with_link_component(
        server.link_absolute
    )


def create_servers_components(type, ranked_only):
    params = {}

    if type:
        params['type'] = type

    if ranked_only:
        params['ranked'] = 'yes'

    return create_single_button_with_link_component(
        url_for('servers_list', **params, _external=True),
        label='Full list on rwrstats.com'
    )


def create_single_button_with_link_component(url, label='Show on rwrstats.com'):
    return [
        ActionRow(
            components=[
                Button(
                    style=ButtonStyles.LINK,
                    url=url,
                    label=label
                )
            ]
        )
    ]
