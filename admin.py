from models import RwrAccount, RwrAccountStat, User, UserFriend, Variable
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user
from flask import redirect, url_for
from rwrs import admin, db, app


class RestrictedView:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.steam_id in app.config['ADMINS']

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))


class RestrictedAdminIndexView(RestrictedView, AdminIndexView):
    pass

class RestrictedModelView(RestrictedView, ModelView):
    pass


admin.add_view(RestrictedModelView(RwrAccount, db.session, name='RWR Accounts', url='rwr-accounts'))
admin.add_view(RestrictedModelView(RwrAccountStat, db.session, name='RWR Accounts Stats', url='rwr-accounts-stats'))
admin.add_view(RestrictedModelView(User, db.session, name='Users', url='users'))
admin.add_view(RestrictedModelView(UserFriend, db.session, name='Users Friends', url='users-friends'))
admin.add_view(RestrictedModelView(Variable, db.session, name='Variables', url='variables'))