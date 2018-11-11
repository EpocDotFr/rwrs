from flask_restful import abort
from rwrs import app
from . import auth


@auth.verify_token
def verify_token(token):
    if token in app.config['API_TOKENS']:
        return True

    return False


@auth.error_handler
def auth_error():
    abort(403, message='Invalid token')
