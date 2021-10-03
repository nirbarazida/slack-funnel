from slack_funnel_app.database.schema import UserTable

#check first user
user = UserTable.query.first()
assert user.username == "nir"