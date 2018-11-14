from flask_limiter.util import get_ipaddr
from flask_httpauth import HTTPTokenAuth
from flask_restful import Api, abort
from flask_limiter import Limiter
from functools import wraps
from rwrs import app
from flask import g
import os


def check_under_maintenance(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if os.path.exists('maintenance'):
            abort(503, message='Maintenance in progress')

        return f(*args, **kwargs)

    return decorated


def rate_limiter_key_func():
    current_token = g.current_token if 'current_token' in g else ''

    return '|'.join([get_ipaddr(), current_token])


auth = HTTPTokenAuth(scheme='Token')
limiter = Limiter(app, key_func=rate_limiter_key_func, headers_enabled=True)
api = Api(app, prefix='/api', catch_all_404s=True, decorators=[
    check_under_maintenance,
    auth.login_required,
    limiter.limit('1/second', error_message='You reached the limit of one request per second')
])

from . import routes, hooks
