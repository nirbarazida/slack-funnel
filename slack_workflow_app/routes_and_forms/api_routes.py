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


@app.route("/api/AddMessage", methods=['POST'])
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
                              created_by=user.id, channel=message_json["channel"], )
        if "direct_user_id" in message_json:
            message = Message(name=message_json["message_name"], message=message_json["message_text"],
                              created_by=user.id, direct_user_id=message_json["direct_user_id"])
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


@app.route("/api/AddWorkflow", methods=['POST'])
@api_auth
def add_workflow_api():
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


@app.route("/api/AddWorkspace", methods=['POST'])
@api_auth
def add_workspace_api():
    """
    {"workspace_name":"", "start_date":"<DATE_TIME_FORMAT>","token":"",workflow_id:""}
    :return:
    """
    input_validation = validate_add_workspace_request(request)

    if input_validation["status"] == False:
        return input_validation["message"]

    if request.is_json:
        user = UserTable.query.filter_by(username=request.authorization.username).first()
        workspace_json = request.get_json()
        workspace_start_time = datetime.strptime(workspace_json["start_date"], DATE_TIME_FORMAT_DB)
        workspace = Workspace(name=workspace_json["workspace_name"],
                              start_date=workspace_start_time,
                              token=workspace_json["token"],
                              created_by=user.id)  # todo: Guy encrypt token
        db.session.add(workspace)
        db.session.commit()

        workspace_id = Workspace.query.filter_by(name=workspace_json["workspace_name"]).first().id

        create_workspace_messages(workspace_id, workspace_start_time, workspace_json["workflow_id"])

        return f"Workspace created successfully. It's id is: {workspace_id}, and it's messages id are"  # todo: change