from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token='xoxp-2572097408081-2556515658997-2552773353590-cf0beece3cb76287207f26912309336b')


message= """Hi #dagshub,
My name is Nir, and I'm a Data Scientist @ DagsHub. :v:
Following the live Q&A session with @Dean Pleban, we are still missing some users who didn't complete the <https://dagshub.com/docs/workshops/interactive-session/|interactive walkthrough session>.
The session will help you understand how DagsHub makes your life easier by managing all the project components under one roof.
Please complete the session and share your DagsHub repos under this thread.
Feel free to reach out here or via DM with any question that comes to mind :mortar_board: 
"""


try:
    response = client.chat_postMessage(channel='#general', text=message,as_user=True,username="Nir Barazida")
    print(response)
except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["ok"] is False
    assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
    print(f"Got an error: {e.response['error']}")

