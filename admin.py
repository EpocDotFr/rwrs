from models import RwrAccount, RwrAccountStat, User, UserFriend, Variable
from flask_admin.contrib.sqla import ModelView
from rwrs import admin, db

admin.add_view(ModelView(RwrAccount, db.session, name='RWR Accounts', url='rwr-accounts'))
admin.add_view(ModelView(RwrAccountStat, db.session, name='RWR Accounts Stats', url='rwr-accounts-stats'))
admin.add_view(ModelView(User, db.session, name='Users', url='users'))
admin.add_view(ModelView(UserFriend, db.session, name='Users Friends', url='users-friends'))
admin.add_view(ModelView(Variable, db.session, name='Variables', url='variables'))
