from flask_limiter.util import get_ipaddr
from flask_httpauth import HTTPTokenAuth
from flask_restful import Api, abort
from flask_limiter import Limiter
from functools import wraps
from rwrs import app
from flask import g


def check_under_maintenance(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.UNDER_MAINTENANCE:
            abort(503, message='Maintenance in progress')

        return f(*args, **kwargs)

    return decorated


def rate_limiter_key_func():
    return '|'.join([
        get_ipaddr(),
        '' # TODO Use current user ID
    ])


auth = HTTPTokenAuth(scheme='Token')
limiter = Limiter(app, key_func=rate_limiter_key_func)
api = Api(app, prefix='/api', catch_all_404s=True, decorators=[
    check_under_maintenance,
    auth.login_required,
    limiter.limit('1/second', error_message='You reached the limit of one request per second')
])

from . import routes, hooks
