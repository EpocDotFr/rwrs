from flask_restful import abort
from models import User
from . import auth


@auth.verify_token
def verify_token(token):
    if not token:
        return False

    try:
        user = User.get_by_pat(token)
    except ValueError:
        return False

    if not user:
        return False

    return user


@auth.error_handler
def auth_error():
    abort(403, message='Invalid Personal Access Token or Personal Access Token not provided')
