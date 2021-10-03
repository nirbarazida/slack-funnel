from slack_workflow_app.database.schema import *

#check first user
user = UserTable.query.all()
print(user)

workflowmessage = WorkflowMessage.query.all()
print(workflowmessage)

workflows = Workflow.query.all()
print(workflows[0].name)


### add_workflow using API ###

import requests
workflow = {"workflow_name": "Omdena basic 5",
            "workflow_messages":
                                [{"message_id": 1, "time_from_start_days": 5, "time_from_start_hours": 1},
                                 {"message_id": 2, "time_from_start_days": 7, "time_from_start_hours": 0}]}

resp = requests.post("http://127.0.0.1:5000/add_workflow/api", json=workflow,auth=('nir@dagshub.com', '123'))
print(str(resp.content))
