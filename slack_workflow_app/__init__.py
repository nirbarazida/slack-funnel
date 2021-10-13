from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from datetime import datetime
import time
import os


from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from slack_workflow_app.const import DB_PATH, SCHEDULER_URL
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/slack_workflow_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Do not move up - it needs to be called AFTER the app is created.
from slack_workflow_app.routes_and_forms import routes

if not os.path.exists(DB_PATH):
    db.create_all()

# Do not move up - it needs to be called AFTER the db is created.
from slack_workflow_app.database.schema import WorkspaceMessage, Workspace, Message


def send_msg(workspace_message):
    """
    recives an WorkspaceMessage object that needs to be sent.
    Sending the message on Slack in DM or channel
    """

    workspace = Workspace.query.filter_by(id=workspace_message.workspace_id).first()
    message = Message.query.filter_by(id=workspace_message.message_id).first()

    if workspace and message:
        client = WebClient(token=workspace.token)

        # Send message to a channel
        if message.channel:
            try:
                response = client.chat_postMessage(channel='#'+message.channel, text=message.message,
                                                   as_user=True)
                print(f"Message send with response: {response}")

            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
                print(f"Got an error: {e.response['error']}")

        #send DM
        else:

            # user_info = client.users_lookupByEmail(email="nir@dagshub.com") #todo: delete
            try:
                response = client.chat_postMessage(channel=message.direct_user_id, text=message.message,
                                                   as_user=True)

                print(f"Message send with response: {response}")

            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
                print(f"Got an error: {e.response['error']}")


def check_messages():
    """
    Iterates over WorkspaceMessage table that holds all the timed messages. Each message that its time passed will be
    sent to the send_msg function that will send on the Slack channel / DM.
    """
    messages = WorkspaceMessage.query.all()
    for message in messages:
        if message.time_utc < datetime.utcnow():
            print(f"Sending message {message.id}")
            send_msg(message)

            print(f"Deleting message {message.id}")
            db.session.delete(message)
            db.session.commit()


def execute_message_check():
    print("Hi, execute message check is on")
    while True:
        time.sleep(10)
        check_messages()


executor.submit(execute_message_check)



