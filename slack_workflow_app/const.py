import os

DB_NAME = "slack_workflow_database.db"
SCHEDULER_URL = "sqlite:///database/scheduler.db"
DB_PATH = os.path.join("database", DB_NAME)

DATE_TIME_FORMAT_FORM = "%Y-%m-%dT%H:%M"
DATE_TIME_FORMAT_DB = "%d-%m-%y %H:%M"

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