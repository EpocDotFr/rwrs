from wtforms.validators import ValidationError
from wtforms import StringField, SelectField
from flask_wtf import FlaskForm
from models import RwrAccount
import wtforms.validators as validators
import rwr.constants
import rwr.scraper


class PlayerClaimForm(FlaskForm):
    type = SelectField('RWR account type', [validators.DataRequired()], choices=[('', '- Please select -')] + [(database, database_info['name']) for database, database_info in rwr.constants.PLAYERS_LIST_DATABASES.items()])
    username = StringField('RWR account username', [validators.DataRequired(), validators.Length(max=16)])

    def validate_username(form, field):
        database = form.type.data
        username = field.data.upper()

        player_exist = rwr.scraper.search_player_by_username(database, username, check_exist_only=True)

        if not player_exist:
            raise ValidationError('This RWR account doesn\'t exist.')

        rwr_account = RwrAccount.get_by_type_and_username(database, username)

        if rwr_account and rwr_account.user_id:
            raise ValidationError('You cannot claim an already claimed RWR account.')

        servers = rwr.scraper.filter_servers(database=database, username=username)

        if servers:
            server = servers[0] # There can be only one

            raise ValidationError('You cannot claim this RWR account as it\'s currently connected on a ranked (official) server ({}).'.format(server.name))
