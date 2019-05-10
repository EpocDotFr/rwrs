from wtforms import StringField, SelectField, BooleanField
from wtforms.validators import ValidationError
from flask_login import current_user
from flask import url_for, flash
from flask_wtf import FlaskForm
from models import RwrAccount
from rwrs import db
import wtforms.validators as validators
import rwr.constants
import rwr.scraper


class RwrsForm(FlaskForm):
    def flash_errors(self):
        """Create a flash error message containing this Form's errors in HTML."""
        if not self.errors:
            return

        message = [
            '<h4 class="mbs">Not so fast!</h4>',
            '<ul>'
        ]

        for field, errors in self.errors.items():
            message.append('<li>{}<ul>'.format(self[field].label.text))

            for error in errors:
                message.append('<li>{}</li>'.format(error))

            message.append('</ul></li>')

        message.append('</ul>')

        flash(''.join(message), 'error')


class PlayerClaimForm(RwrsForm):
    type = SelectField('RWR account type', [validators.DataRequired()], choices=[('', '- Please select -')] + [(database, database_info['name']) for database, database_info in rwr.constants.PLAYERS_LIST_DATABASES.items()])
    username = StringField('RWR account username', [validators.DataRequired(), validators.Length(max=16)])

    def validate_username(form, field):
        database = form.type.data
        username = field.data.upper()

        player_exist = rwr.scraper.search_player_by_username(database, username, check_exist_only=True)

        if not player_exist:
            raise ValidationError('This RWR account doesn\'t exist.')

        rwr_account = RwrAccount.get_by_type_and_username(database, username)

        if rwr_account:
            if rwr_account.user_id:
                raise ValidationError('This RWR account has already been claimed{}.'.format(
                    ' by yourself' if rwr_account.user_id == current_user.id else ' by <strong>{}</strong>'.format(rwr_account.user.username) if rwr_account.user.is_profile_public else ''
                ))

            if rwr_account.claim_initiated_by_user_id:
                if rwr_account.has_claim_expired():
                    db.session.add(rwr_account)
                    db.session.commit()
                else:
                    if rwr_account.claim_initiated_by_user_id == current_user.id:
                        raise ValidationError('You are already claiming this RWR account, <a href="{}">click here</a> to continue.'.format(url_for('player_finalize_claim', rwr_account_id=rwr_account.id)))
                    else:
                        raise ValidationError('This RWR account is already being claimed.')

        servers = rwr.scraper.filter_servers(database=database, username=username)

        if servers:
            server = servers[0] # There can only be one

            raise ValidationError('You cannot claim this RWR account as it\'s currently connected on a ranked (official) server ({}).'.format(server.name))


class UserGeneralSettingsForm(RwrsForm):
    is_profile_public = BooleanField('Set my RWRS account as public', default=False)

    def populate_user(self, user):
        """Set the User attributes from this form values."""
        user.is_profile_public = self.is_profile_public.data


class UserFriendForm(RwrsForm):
    username = StringField('Player name', [validators.DataRequired(), validators.Length(max=16)])

    def validate_username(form, field):
        if field.data.startswith(' ') or field.data.endswith(' '):
            raise ValidationError('Spaces aren\'t allowed')

        username = field.data.upper()

        if current_user.get_friend(username):
            raise ValidationError('{} is already present in your friends list'.format(username))
