from flask_restful import Resource, marshal_with, abort
from models import RwrAccount, RwrAccountStat
from . import api, transformers, validators
from types import SimpleNamespace
from rwr.player import Player
from flask import url_for, g
from rwrs import app
import rwr.constants
import rwr.scraper


class ServersResource(Resource):
    @staticmethod
    def replace_true_by_yes(dct, key):
        if key in dct and dct[key] is True:
            dct[key] = 'yes'

    @marshal_with(transformers.server_simple)
    def get(self):
        args = validators.get_servers_list.parse_args()

        if args:
            ServersResource.replace_true_by_yes(args, 'dedicated')
            ServersResource.replace_true_by_yes(args, 'ranked')
            ServersResource.replace_true_by_yes(args, 'not_empty')
            ServersResource.replace_true_by_yes(args, 'not_full')

            servers = rwr.scraper.filter_servers(**args)
        else:
            servers = rwr.scraper.get_servers()

        return servers


class ServerResource(Resource):
    @staticmethod
    def replace_players_usernames_by_objects(server):
        server.players.list = [SimpleNamespace(
            username=player_username,
            link_absolute=url_for('player_details', database=server.database, username=player_username, _external=True) if server.is_ranked and server.database else None,
            is_me=player_username.lower() == app.config['MY_USERNAME'],
            is_contributor=player_username.lower() in app.config['CONTRIBUTORS'],
            is_rwr_dev=player_username.lower() in app.config['DEVS'],
            is_ranked_servers_admin=player_username.lower() in app.config['RANKED_SERVERS_ADMINS'],
            database=server.database,
            database_name=server.database_name
        ) for player_username in server.players.list]

    @marshal_with(transformers.server_full)
    def get(self, ip, port):
        server = rwr.scraper.get_server_by_ip_and_port(ip, port)

        if not server:
            abort(404, message='Server not found')

        ServerResource.replace_players_usernames_by_objects(server)

        return server


class PlayersResource(Resource):
    @marshal_with(transformers.player_list)
    def get(self, database):
        args = validators.get_players_list.parse_args()

        players = rwr.scraper.get_players(
            database,
            sort=args['sort'],
            target=args['target'],
            start=args['start'],
            limit=args['limit']
        )

        if args['target'] and not players:
            abort(404, message='Target player not found')

        servers = rwr.scraper.get_servers()

        for player in players:
            player.set_playing_on_server(servers)

        return players


class PlayerResource(Resource):
    @marshal_with(transformers.player_full)
    def get(self, database, username):
        args = validators.get_one_player.parse_args()

        if args['date']: # Stats history lookup mode
            player_exist = rwr.scraper.search_player_by_username(database, username, check_exist_only=True)

            if not player_exist:
                abort(404, message='Player not found')

            rwr_account = RwrAccount.get_by_type_and_username(database, username)

            if not rwr_account:
                abort(412, message='Stats history unavailable for this player')

            rwr_account_stat = RwrAccountStat.get_stats_for_date(rwr_account.id, args['date'])

            if not rwr_account_stat:
                abort(404, message='No stats found for the given date')

            player = Player.craft(rwr_account, rwr_account_stat)
            player.created_at = args['date']
            player.promoted_to_rank = rwr_account_stat.promoted_to_rank
        else: # Live data mode
            player = rwr.scraper.search_player_by_username(database, username)

            if not player:
                abort(404, message='Player not found')

        servers = rwr.scraper.get_servers()

        player.set_playing_on_server(servers)

        return player


class LiveCountersResource(Resource):
    @marshal_with(transformers.live_counters)
    def get(self):
        return SimpleNamespace(
            players=SimpleNamespace(
                total=g.total_players,
                online=g.online_players
            ),
            servers=SimpleNamespace(
                total=g.total_servers,
                active=g.active_servers
            )
        )


api.add_resource(ServersResource, '/servers')
api.add_resource(ServerResource, '/servers/<ip>:<int:port>')
api.add_resource(PlayersResource, '/players/<any({}):database>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
api.add_resource(PlayerResource, '/players/<any({}):database>/<username>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
api.add_resource(LiveCountersResource, '/live-counters')
