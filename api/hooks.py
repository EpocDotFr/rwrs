from flask_restful import abort
from rwrs import app
from flask import g
from . import auth


@auth.verify_token
def verify_token(token):
    if token in app.config['API_TOKENS']:
        g.current_token = token

        return True

    return False


@auth.error_handler
def auth_error():
    abort(403, message='Invalid token or token not provided')
