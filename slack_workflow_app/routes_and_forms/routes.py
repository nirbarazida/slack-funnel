from flask import render_template, url_for, flash, redirect, request, jsonify
from slack_workflow_app.routes_and_forms.forms import RegistrationForm, LoginForm, NewMessageForm, NewMWorkspaceForm
from slack_workflow_app import app, db, bcrypt
from slack_workflow_app.database.schema import UserTable, Workspace, Workflow, WorkflowMessage, Message, \
    WorkspaceMessage
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
from functools import wraps
from slack_workflow_app.const import DATE_TIME_FORMAT_FORM, DATE_TIME_FORMAT_DB,posts
from slack_sdk import WebClient, errors
from slack_workflow_app.secret_const import CLIENT_ID, CLIENT_SECRET
import json

# todo: use bcrypt for the tokens
# todo: add login_required to relevent pages





@app.route("/")
@app.route("/home")
def home():
    # workspace = Workspace.query.all() #todo : query only the active ones (concat with workspace mes and check who's status is wating"
    return render_template('home/home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about/about.html', posts=posts, tab_title="About-nir")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = UserTable(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in!', 'success')
        return redirect(url_for('login'))
    return render_template('register/register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = UserTable.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login/login.html', title='Login', form=form)


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    return render_template('account/account.html', title='Account')


@app.route("/AddMessage", methods=['GET', 'POST'])
@login_required
def add_message():  # todo: add channel and direct_user_email
    form = NewMessageForm()
    if form.validate_on_submit():
        message = Message(name=form.message_name.data, message=form.message.data, created_by=current_user.id)
        db.session.add(message)
        db.session.commit()
        flash('Your message has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('AddMessage/AddMessage.html', title='New Message', form=form, legend='New Message')


def convert_slack_sdk_to_json(response):
    # todo BUG: slack-sdk has a bug that the error retunns an object and not a jsom
    return response[response.index("{"): response.rfind("}") + 1].replace("'", '"').lower().replace("none","null")


def extract_token(code, client_id, client_secret):  # todo: save the client & client_secret on diffrent table

    client = WebClient()

    try:
        response = client.oauth_v2_access(
            code=code,
            client_id=client_id,
            client_secret=client_secret)
        return json.loads(convert_slack_sdk_to_json(str(response)))
    except errors.SlackApiError as e:
        return json.loads(convert_slack_sdk_to_json(str(e)))


@app.route("/AddWorkspace", methods=['GET', 'POST'])
@login_required
def add_workspace():
    form = NewMWorkspaceForm()
    if form.validate_on_submit():
        # datetime.strptime(format_start_date_str, DATE_TIME_FORMAT_DB)

        # format_start_date_str = form.start_date.data.strftime(
        #     DATE_TIME_FORMAT_DB)  # todo BUG: due to bag - When sending the form it doesn't recognize any other format than "%Y-%m-%dT%H:%M", but this format gives errors wit SQL alchemy so I convet it back to the DB format
        client_id = form.client_id.data if form.client_id.data else CLIENT_ID
        client_secret = form.client_secret.data if form.client_id.data else CLIENT_SECRET

        response = extract_token(form.code_for_token.data, client_id, client_secret)

        if not response["ok"]:
            flash(f'{response["error"]}', 'danger')
            return redirect(url_for('add_workspace'))

        workspace = Workspace(name=form.workspace_name.data,
                              start_date=form.start_date.data, token=response["authed_user"]["access_token"],
                              created_by=current_user.id)

        db.session.add(workspace)
        db.session.commit()
        flash('The workspace has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('AddWorkspace/AddWorkspace.html', title='New Workspace', form=form, legend='New Workspace')



