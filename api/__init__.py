from flask_httpauth import HTTPTokenAuth
from flask_restful import Api, abort
from functools import wraps
from rwrs import app
import os


def check_under_maintenance(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if os.path.exists('maintenance'):
            abort(503)

        return f(*args, **kwargs)

    return decorated


auth = HTTPTokenAuth(scheme='Token')
api = Api(app, prefix='/api', catch_all_404s=True, decorators=[check_under_maintenance, auth.login_required])

from . import routes, hooks
