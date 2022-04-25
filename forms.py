from wtforms.validators import ValidationError
from wtforms import StringField, BooleanField
from flask_login import current_user
from flask_wtf import FlaskForm
import wtforms.validators as validators


class UserGeneralSettingsForm(FlaskForm):
    is_profile_public = BooleanField('Set my RWRS account as public', default=False)

    def populate_user(self, user):
        """Set the User attributes from this form values."""
        user.is_profile_public = self.is_profile_public.data


class UserFriendForm(FlaskForm):
    username = StringField('Player name', [validators.DataRequired(), validators.Length(max=16)])

    def validate_username(form, field):
        username = field.data.upper()

        if current_user.has_friend(username):
            raise ValidationError('{} is already your friend'.format(username))


class RwrAccountDeleteForm(FlaskForm):
    username_confirmation = StringField('Player name confirmation', [validators.DataRequired(), validators.Length(max=16)])

    def __init__(self, target_username):
        super().__init__()

        self.target_username = target_username

    def validate_username_confirmation(form, field):
        if field.data != form.target_username:
            raise ValidationError('Username does not match')
