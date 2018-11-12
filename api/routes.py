from flask_restful import Resource, marshal_with, abort
from . import api, transformers, validators
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
    @marshal_with(transformers.server_full)
    def get(self, ip, port):
        server = rwr.scraper.get_server_by_ip_and_port(ip, port)

        if not server:
            abort(404, message='Server not found')

        return server

api.add_resource(ServersResource, '/servers')
api.add_resource(ServerResource, '/servers/<ip>:<int:port>')
