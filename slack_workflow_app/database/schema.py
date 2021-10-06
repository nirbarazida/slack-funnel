from slack_workflow_app import db, login_manager
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship

@login_manager.user_loader
def load_user(user_id):
    return UserTable.query.get(int(user_id))


class UserTable(db.Model, UserMixin):
    """
    stores all the user that was register to the website.
    relationship:
        Email - one to many
    """

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(30), nullable=False, unique=True)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return str(self.id)
        except AttributeError:
            raise NotImplementedError('No `id` attribute - override `get_id`')

class Workspace(db.Model):
    __tablename__ = 'workspaces'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    start_date = db.Column(db.DateTime(), default=datetime.utcnow)
    token = db.Column(db.String(150), nullable=False, unique=True)

    # many 2 many: Workspace -> WorkspaceMessage <- Message
    message = relationship("WorkspaceMessage", backref='workspace')

    # one 2 many: 1 workflow - workspace N
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'))
    workflow = relationship("Workflow",back_populates="workspace")

    created_by = db.Column(db.String(30), nullable=False)


class Workflow(db.Model):
    __tablename__ = 'workflows'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)

    # many 2 many - Workflow -> WorkflowMessage <- Message
    message = relationship("WorkflowMessage", backref='workflow')

    # one 2 many - 1 workflow - workspace N
    workspace = relationship("Workspace",back_populates="workflow")

    created_by = db.Column(db.String(30), nullable=False)


class WorkflowMessage(db.Model):
    __tablename__ = 'workflow_messages'
    id = db.Column(db.Integer, primary_key=True)
    time_from_start_days = db.Column(db.Integer, nullable=False)
    time_from_start_hours = db.Column(db.Integer, nullable=False)

    # many 2 many - Workflow -> WorkflowMessage <- Message
    workflow_id = db.Column(db.Integer(), db.ForeignKey("workflows.id"))
    message_id = db.Column(db.Integer(), db.ForeignKey("messages.id"))

    # one 2 one - WorkflowMessage (ID) - WorkspaceMessage (NonID)
    workspace_message = relationship('WorkspaceMessage', backref='workflowmessage', uselist=False)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    message = db.Column(db.String(2000), nullable=False, unique=True)

    # many 2 many - Workspace -> WorkspaceMessage <- Message
    workspace = relationship("WorkspaceMessage", backref='message')

    # many 2 many - Workflow -> WorkflowMessage <- Message
    workflow = relationship("WorkflowMessage", backref='message')

    created_by = db.Column(db.String(30), nullable=False)

class WorkspaceMessage(db.Model):
    __tablename__ = 'workspace_messages'
    id = db.Column(db.Integer, primary_key=True)
    time_utc = db.Column(db.DateTime(), nullable=False)
    status = db.Column(db.Boolean, default=0)  # todo check that it works + fill with 0 or 1 not T/F

    # many 2 many - Workspace -> WorkspaceMessage <- Message
    workspace_id = db.Column(db.Integer(), db.ForeignKey("workspaces.id"))
    message_id = db.Column(db.Integer(), db.ForeignKey("messages.id"))

    # one 2 one - WorkflowMessage (ID) - WorkspaceMessage (NonID)
    workflow_message_id = db.Column(db.Integer(), db.ForeignKey('workflow_messages.id'))