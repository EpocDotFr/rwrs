from flask_limiter.util import get_remote_address
from flask_httpauth import HTTPTokenAuth
from flask_restful import Api, abort
from flask_limiter import Limiter
from flask import g, request
from functools import wraps
from rwrs import app

http_auth_scheme = 'Token'


def check_under_maintenance(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.UNDER_MAINTENANCE:
            abort(503, message='Maintenance in progress')

        return f(*args, **kwargs)

    return decorated


def get_current_pat():
    """Retrieve the current PAT used in the request."""
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return ''

    auth_header_parts = auth_header.split(' ', maxsplit=1)

    if not auth_header_parts or len(auth_header_parts) != 2 or auth_header_parts[0] != http_auth_scheme:
        return ''

    return auth_header_parts[1].strip()


def rate_limiter_key_func():
    return '|'.join([
        get_remote_address(),
        get_current_pat()
    ])


auth = HTTPTokenAuth(scheme=http_auth_scheme)
limiter = Limiter(rate_limiter_key_func, app=app)
api = Api(app, prefix='/api', catch_all_404s=True, decorators=[
    check_under_maintenance,
    auth.login_required,
    limiter.limit('1/second', error_message='You reached the limit of one request per second')
])

from . import routes, hooks
