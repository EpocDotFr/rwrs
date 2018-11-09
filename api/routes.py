from flask_restful import Resource, marshal_with
from . import api, transformers
import rwr.scraper


class ServersResource(Resource):
    @marshal_with(transformers.server_fields)
    def get(self):
        return rwr.scraper.get_servers()


api.add_resource(ServersResource, '/servers')
