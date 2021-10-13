from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, optional, ValidationError
from slack_workflow_app.database.schema import UserTable, Workspace, Workflow, WorkflowMessage, Message, \
    WorkspaceMessage
from wtforms.fields.html5 import DateTimeLocalField
from datetime import datetime
from slack_workflow_app.const import DATE_TIME_FORMAT_FORM


# todo: add validate step to all relevent forms - add step


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = UserTable.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = UserTable.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class NewMessageForm(FlaskForm):  # todo: validate that one of the channel/ direct_user_id exists
    message_name = StringField('Message name', validators=[DataRequired(), Length(min=2, max=30)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=2, max=2000)])
    channel = StringField('Channel name')
    direct_user_id = StringField('User ID (Direct message)')

    submit = SubmitField('Save')

    def validate_message_name(self, message_name):
        user = Message.query.filter_by(name=message_name.data).first()
        if user:
            raise ValidationError('That name is taken. Please choose a different name.')

    def validate_message(self, message):
        message = Message.query.filter_by(message=message.data).first()
        if message:
            raise ValidationError(
                f'This message exists in the data base under the name - "{message.name} with id {message.id}"')


class NewMWorkspaceForm(FlaskForm):
    workspace_name = StringField('Workspace name', validators=[DataRequired(), Length(min=2, max=30)])
    start_date = DateTimeLocalField('Workflow start date and time', format=DATE_TIME_FORMAT_FORM,
                                    validators=[DataRequired()])
    code_for_token = StringField('Code for token',validators=[DataRequired()])
    client_id = StringField('Client ID')
    client_secret = StringField('Client secret')
    submit = SubmitField('Save')

    def validate_workspace_name(self, workspace_name):
        workspace = Workspace.query.filter_by(name=workspace_name.data).first()
        if workspace:
            raise ValidationError('That name is taken. Please choose a different name for the workspace.')

