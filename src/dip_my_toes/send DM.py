import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token='xoxp-2551908125877-2578555240208-2559212431810-79e83280096b4e43ffa918d364b75659')
user_info = client.users_lookupByEmail(email="nir@dagshub.com")
print(user_info['user']['id'])

try:
    response = client.chat_postMessage(channel=user_info['user']['id'], text="Nir2",as_user=True)
    assert response["message"]["text"] == "Nir2"
except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["ok"] is False
    assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
    print(f"Got an error: {e.response['error']}")