from msal_bearer import BearerAuth, get_user_name, get_token

tenantID = "3aa4a235-b6e2-48d5-9195-7fcf05b459b0"
client_id = "dde32392-142b-4933-bd87-ecdd28d7250f"
scope = ["api://dde32392-142b-4933-bd87-ecdd28d7250f/Calculate.All"]

auth = BearerAuth.get_auth(tenantID=tenantID, clientID=client_id, scopes=scope)
token = get_token(tenant_id=tenantID, client_id=client_id, scopes=scope)
print(f"User: {get_user_name()}")
if auth.token == token:
    print("Tokens are equal")
else:
    print("oops")
