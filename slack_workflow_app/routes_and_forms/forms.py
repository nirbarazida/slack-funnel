from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, optional, ValidationError
from slack_workflow_app.database.schema import UserTable, Workspace, Workflow, WorkflowMessage, Message, WorkspaceMessage

#todo: add validate step to all relevent forms - add step


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


class NewMessageForm(FlaskForm): #todo: add channel and direct_user_email
    message_name = StringField('Message name', validators=[DataRequired(), Length(min=2, max=30)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=2, max=2000)])
    submit = SubmitField('Save')

    def validate_message_name(self, message_name):
        user = Message.query.filter_by(name=message_name.data).first()
        if user:
            raise ValidationError('That name is taken. Please choose a different one.')

    def validate_message(self, message):
        message = Message.query.filter_by(message=message.data).first()
        if message:
            raise ValidationError(f'This message exists in the data base under the name - "{message.name}"')



