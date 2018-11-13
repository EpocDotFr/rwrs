from flask_restful import Resource, marshal_with, abort
from . import api, transformers, validators
from types import SimpleNamespace
from flask import url_for
import rwr.scraper


class ServersResource(Resource):
    @marshal_with(transformers.server_simple)
    def get(self):
        filters = validators.get_servers_list.parse_args()

        if filters:
            servers = rwr.scraper.filter_servers(**filters)
        else:
            servers = rwr.scraper.get_servers()

        return servers


class ServerResource(Resource):
    @staticmethod
    def replace_players_usernames_by_objects(server):
        server.players.list = [SimpleNamespace(
            username=player_username,
            link_absolute=url_for('player_details', database=server.database, username=player_username, _external=True) if server.is_ranked and server.database else None
        ) for player_username in server.players.list]

    @marshal_with(transformers.server_full)
    def get(self, ip, port):
        server = rwr.scraper.get_server_by_ip_and_port(ip, port)

        if not server:
            abort(404, message='Server not found')

        ServerResource.replace_players_usernames_by_objects(server)

        return server

api.add_resource(ServersResource, '/servers')
api.add_resource(ServerResource, '/servers/<ip>:<int:port>')
