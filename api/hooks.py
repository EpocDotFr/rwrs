from flask_restful import abort
from models import User
from app import db
from . import auth
import arrow


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

    user.api_last_called_at = arrow.utcnow().floor('second')

    db.session.add(user)
    db.session.commit()

    return user


@auth.error_handler
def auth_error():
    abort(403, message='Invalid Personal Access Token or Personal Access Token not provided')
