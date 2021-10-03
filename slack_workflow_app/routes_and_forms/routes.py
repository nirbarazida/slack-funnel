from flask import render_template, url_for, flash, redirect, request,jsonify
from slack_workflow_app.routes_and_forms.forms import RegistrationForm, LoginForm, NewMessageForm
from slack_workflow_app import app, db, bcrypt
from slack_workflow_app.database.schema import UserTable, Workspace, Workflow, WorkflowMessage, Message, WorkspaceMessage
from flask_login import login_user, current_user, logout_user, login_required

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
def add_message():
    form = NewMessageForm()
    if form.validate_on_submit():
        message = Message(name=form.message_name.data, message=form.message.data, created_by=current_user)
        db.session.add(message)
        db.session.commit()
        flash('Your message has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('add_message/add_message.html', title='New Message', form=form, legend='New Message')



############# API ###############


def validate_add_workflow_request(request): # todo: Simon can it be done cleaner?
    """Validation function for the API request"""

    workflow_json = request.get_json()
    # Workflow name exist in DB

    if Workflow.query.filter_by(name=workflow_json["workflow_name"]).first():
        return {"status": False, "message": "workflow name already exist in the database"}

    # Workflow id doesn't exist in DB
    for message in workflow_json['workflow_messages']:
        if Message.query.filter_by(id=message['message_id']).first() is None:
            return {"status": False, "message": "message doesn't exist in the database"}

    return {"status":True}


@app.route("/add_workflow/api", methods=['GET', 'POST'])
# @login_required # todo: Simon - how to create a post with user Oauth?
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
        workflow_json = request.get_json()
        workflow = Workflow(name=workflow_json["workflow_name"],
                            created_by=1)  # current_user.id) # todo: undo after Oauth fix
        db.session.add(workflow)
        db.session.commit()

        workflow_id = Workflow.query.filter_by(name=workflow_json["workflow_name"]).first().id

        for message in workflow_json['workflow_messages']:
            workflowmessage = WorkflowMessage(workflow_id=workflow_id, message_id=message['message_id'],
                                              time_from_start_days=message['time_from_start_days'],
                                              time_from_start_hours=message['time_from_start_hours'])
            db.session.add(workflowmessage)
            db.session.commit()

        return f"Workflow was created successfully. It's id is: {workflow_id}"
    else:
        return redirect(url_for('home'))  # todo: show informative message before redirect


@app.route("/add_workspace/api", methods=['GET', 'POST'])
# @login_required # todo: Simon - how to create a post with user Oauth?
def add_workspace():
    if request.is_json:
        workflow_json = request.get_json()