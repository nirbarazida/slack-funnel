from flask import render_template, url_for, flash, redirect, request, jsonify
from slack_workflow_app.routes_and_forms.forms import RegistrationForm, LoginForm, NewMessageForm
from slack_workflow_app import app, db, bcrypt
from slack_workflow_app.database.schema import UserTable, Workspace, Workflow, WorkflowMessage, Message, \
    WorkspaceMessage
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
from functools import wraps

# todo: use bcrypt for the tokens
# todo: add login_required to relevent pages


posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]


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


@app.route("/add_message", methods=['GET', 'POST'])
@login_required
def add_message():  # todo: add channel and direct_user_email
    form = NewMessageForm()
    if form.validate_on_submit():
        message = Message(name=form.message_name.data, message=form.message.data, created_by=current_user.id)
        db.session.add(message)
        db.session.commit()
        flash('Your message has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('add_message/add_message.html', title='New Message', form=form, legend='New Message')


############# API ###############

def api_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        if auth:
            user = UserTable.query.filter_by(username=auth.username).first()
            if user and bcrypt.check_password_hash(user.password, auth.password):
                return f(*args, **kwargs)

        return 'Could not verify your login information. Please add auth=(username, password) to your request'

    return decorated


def validate_add_message_request(request):  # todo: Simon can it be done cleaner?
    """Validation function for the API request"""

    message_json = request.get_json()
    # Workflow name exist in DB

    if Message.query.filter_by(name=message_json["message_name"]).first():
        return {"status": False, "message": "Message name already exist in the database"}

    if Message.query.filter_by(message=message_json["message_text"]).first():
        return {"status": False, "message": "Message content already exist in the database"}

    return {"status": True}


@app.route("/api/add_message", methods=['POST'])
@api_auth
def add_message_api():
    input_validation = validate_add_message_request(request)

    if input_validation["status"] == False:
        return input_validation["message"]

    if request.is_json:
        message_json = request.get_json()
        user = UserTable.query.filter_by(username=request.authorization.username).first()
        if "channel" in message_json:
            message = Message(name=message_json["message_name"], message=message_json["message_text"],
                              created_by=user.id, channel=message_json["channel"])
        else:
            message = Message(name=message_json["message_name"], message=message_json["message_text"],
                              created_by=user.id, direct_user_email=message_json["direct_user_email"])
        db.session.add(message)
        db.session.commit()

        message_id = Message.query.filter_by(name=message_json["message_name"]).first().id

        return f"Message created successfully. It's id is: {message_id}"

    else:
        return f"Please add a proper json with message_name, message_text"


def validate_add_workflow_request(request):  # todo: Simon can it be done cleaner?
    """Validation function for the API request"""

    workflow_json = request.get_json()
    # Workflow name exist in DB

    if Workflow.query.filter_by(name=workflow_json["workflow_name"]).first():
        return {"status": False, "message": "workflow name already exist in the database"}

    # Workflow id doesn't exist in DB
    for message in workflow_json['workflow_messages']:
        if Message.query.filter_by(id=message['message_id']).first() is None:
            return {"status": False, "message": "message doesn't exist in the database"}

    return {"status": True}


@app.route("/api/add_workflow", methods=['GET', 'POST'])
@api_auth
def add_workflow():
    """
    import requests
    workflow = {"workflow_name": "Omdena basic 5",
                "workflow_messages":
                                    [{"message_id": 1, "time_from_start_days": 5, "time_from_start_hours": 1},
                                     {"message_id": 2, "time_from_start_days": 7, "time_from_start_hours": 0}]}

    resp = requests.post("http://127.0.0.1:5000/add_workflow/api", json=workflow,auth=('nir@dagshub.com', '123'))
    print(str(resp.content))
    """
    input_validation = validate_add_workflow_request(request)

    if input_validation["status"] == False:
        return input_validation["message"]

    if request.is_json:
        user = UserTable.query.filter_by(username=request.authorization.username).first()

        workflow_json = request.get_json()
        workflow = Workflow(name=workflow_json["workflow_name"],
                            created_by=user.id)
        db.session.add(workflow)
        db.session.commit()

        workflow_id = Workflow.query.filter_by(name=workflow_json["workflow_name"]).first().id

        for message in workflow_json['workflow_messages']:
            workflowmessage = WorkflowMessage(workflow_id=workflow_id, message_id=message['message_id'],
                                              time_from_start_days=message['time_from_start_days'],
                                              time_from_start_hours=message['time_from_start_hours'])
            db.session.add(workflowmessage)
            db.session.commit()

        return f"Workflow created successfully. It's id is: {workflow_id}"
    else:
        return redirect(url_for('home'))  # todo: show informative message before redirect


def validate_add_workspace_request(request):  # todo: Simon can it be done cleaner?
    """Validation function for the API request"""

    workspace_json = request.get_json()
    # Workflow name exist in DB

    if Workspace.query.filter_by(name=workspace_json["workspace_name"]).first():
        return {"status": False, "message": "workspace name already exist in the database"}

    if Workflow.query.filter_by(id=workspace_json["workflow_id"]).first() is None:
        return {"status": False, "message": "workflow id doesn't exist in the database"}

    return {"status": True}


def create_workspace_messages(workspace_id, start_time, workflow_id):
    workflow_messages = WorkflowMessage.query.filter_by(workflow_id=workflow_id)

    for workflow_message in workflow_messages:

        execute_time = start_time + timedelta(days=workflow_message.time_from_start_days,
                                              hours=workflow_message.time_from_start_hours)

        if execute_time + timedelta(minutes=1) < datetime.utcnow():
            # todo: add logic role
            print("You want to set a message before the current time?")
        else:
            workspace_message = WorkspaceMessage(time_utc=execute_time, status=0,
                                                 workspace_id=workspace_id, message_id=workflow_message.id,
                                                 workflow_message_id=workflow_message.id)  # todo check status =0 and not False
            print(workspace_message)
            db.session.add(workspace_message)
            db.session.commit()


@app.route("/api/add_workspace", methods=['GET', 'POST'])
@api_auth
def add_workspace():
    """
    {"workspace_name":"", "start_date":"%d/%m/%y %H:%M","token":"",workflow_id:""}
    :return:
    """
    input_validation = validate_add_workspace_request(request)

    if input_validation["status"] == False:
        return input_validation["message"]

    if request.is_json:
        user = UserTable.query.filter_by(username=request.authorization.username).first()
        workspace_json = request.get_json()
        workspace_start_time = datetime.strptime(workspace_json["start_date"], '%d/%m/%y %H:%M')
        workspace = Workspace(name=workspace_json["workspace_name"],
                              start_date=workspace_start_time,
                              token=workspace_json["token"],
                              created_by=user.id)  # todo: Guy encrypt token
        db.session.add(workspace)
        db.session.commit()

        workspace_id = Workspace.query.filter_by(name=workspace_json["workspace_name"]).first().id

        create_workspace_messages(workspace_id, workspace_start_time, workspace_json["workflow_id"])

        return f"Workspace created successfully. It's id is: {workspace_id}, and it's messages id are"  # todo: change
