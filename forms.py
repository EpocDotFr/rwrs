from wtforms import StringField, SelectField
from flask_wtf import FlaskForm
import wtforms.validators as validators
import rwr.constants


class PlayerClaimForm(FlaskForm):
    type = SelectField('RWR account type', [validators.DataRequired()], choices=[('', 'Please select a type')] + [(database, database_info['name']) for database, database_info in rwr.constants.PLAYERS_LIST_DATABASES.items()])
    username = StringField('RWR account username', [validators.DataRequired(), validators.Length(max=16)])
