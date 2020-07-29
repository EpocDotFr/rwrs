from flask_restful import Resource, marshal_with, abort
from models import RwrAccount, RwrAccountStat, User
from . import api, transformers, validators
from types import SimpleNamespace
from rwr.player import Player
from flask import url_for, g
from rwrs import db
import rwr.constants
import rwr.scraper
import helpers


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

        for server in servers:
            server.has_friends = server.has_friends_from_user(g.current_user)

        return servers


class ServerResource(Resource):
    @staticmethod
    def replace_players_usernames_by_objects(server):
        server.players.list = [SimpleNamespace(
            username=player_username,
            link_absolute=url_for('player_details', database=server.database, username=player_username, _external=True) if server.is_ranked and server.database else None,
            is_myself=helpers.is_player_myself(player_username),
            is_contributor=helpers.is_player_contributor(player_username),
            is_rwr_dev=helpers.is_player_rwr_dev(player_username),
            is_ranked_servers_mod=helpers.is_player_ranked_server_mod(player_username),
            database=server.database,
            database_name=server.database_name,
            is_friend=g.current_user.has_friend(player_username)
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
            player.is_friend = player.is_friend_with_user(g.current_user)

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
        player.is_friend = player.is_friend_with_user(g.current_user)

        return player


class PlayerStatsHistoryResource(Resource):
    @marshal_with(transformers.player_stats_history)
    def get(self, database, username):
        args = validators.get_player_stats_history.parse_args()

        player = rwr.scraper.search_player_by_username(database, username)

        if not player:
            abort(404, message='Player not found')

        if not player.rwr_account:
            abort(412, message='Stats history unavailable for this player')

        return player.rwr_account.ordered_stats.paginate(
            page=args['page'],
            per_page=args['limit'],
            error_out=False
        ).items


class LiveCountersResource(Resource):
    @marshal_with(transformers.live_counters)
    def get(self):
        return SimpleNamespace(
            players=SimpleNamespace(
                total=g.total_players,
                online=g.online_players,
                friends_online=g.current_user.number_of_playing_friends
            ),
            servers=SimpleNamespace(
                total=g.total_servers,
                active=g.active_servers
            )
        )


class UserResource(Resource):
    @marshal_with(transformers.user_full)
    def get(self, user_id):
        user = User.query.get(user_id)

        if not user or not user.is_profile_public:
            abort(404, message='User not found')

        return user


class FriendsResource(Resource):
    @marshal_with(transformers.friend)
    def get(self):
        return g.current_user.friends_ordered_by_username

    @marshal_with(transformers.friend)
    def post(self):
        args = validators.add_friend.parse_args()

        if g.current_user.has_friend(args['username']):
            abort(412, message='{} is already your friend'.format(args['username']))

        user_friend = g.current_user.add_friend(args['username'])

        db.session.commit()

        return user_friend, 201


class FriendResource(Resource):
    def delete(self, username):
        if g.current_user.remove_friend(username):
            db.session.commit()

            return '', 204
        else:
            abort(404, message='{} is not your friend'.format(username))

api.add_resource(ServersResource, '/servers')
api.add_resource(ServerResource, '/servers/<ip>:<int:port>')
api.add_resource(PlayersResource, '/players/<any({}):database>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
api.add_resource(PlayerResource, '/players/<any({}):database>/<path:username>'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
api.add_resource(PlayerStatsHistoryResource, '/players/<any({}):database>/<path:username>/stats-history'.format(rwr.constants.VALID_DATABASES_STRING_LIST))
api.add_resource(FriendsResource, '/friends')
api.add_resource(FriendResource, '/friends/<path:username>')
api.add_resource(UserResource, '/users/<int:user_id>')
api.add_resource(LiveCountersResource, '/live-counters')
