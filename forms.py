from wtforms.validators import ValidationError
from wtforms import StringField, SelectField
from flask_wtf import FlaskForm
from models import RwrAccount
import wtforms.validators as validators
import rwr.constants
import rwr.scraper


class PlayerClaimForm(FlaskForm):
    type = SelectField('RWR account type', [validators.DataRequired()], choices=[('', 'Please select a type')] + [(database, database_info['name']) for database, database_info in rwr.constants.PLAYERS_LIST_DATABASES.items()])
    username = StringField('RWR account username', [validators.DataRequired(), validators.Length(max=16)])

    def validate_username(form, field):
        player_exist = rwr.scraper.search_player_by_username(form.type.data, field.data, check_exist_only=True)

        if not player_exist:
            raise ValidationError('This RWR account doesn\'t exist.')

        rwr_account = RwrAccount.get_by_type_and_username(form.type.data, field.data)

        if rwr_account:
            pass # TODO Check if RwrAccount already claimed: if yes, abort
