from msal_bearer import Authenticator, BearerAuth, get_user_name, get_token

tenantID = "3aa4a235-b6e2-48d5-9195-7fcf05b459b0"
client_id = "98fe146b-2687-4db9-9c84-45f4cd9063af"
scope = ["api://dde32392-142b-4933-bd87-ecdd28d7250f/Calculate.All"]

auth = BearerAuth.get_auth(tenantID=tenantID, clientID=client_id, scopes=scope)
token = get_token(tenant_id=tenantID, client_id=client_id, scopes=scope)
print(f"User: {get_user_name()}")
if auth.token == token:
    print("Tokens are equal")
else:
    print("oops")

auth = Authenticator(tenant_id=tenantID, client_id=client_id, scopes=scope)
token_3 = auth.get_token()
if token_3 == token:
    print("Tokens are equal")

auth.set_token(token_3)
token_4 = auth.get_token()
if token_4 == token:
    print("Tokens are equal")
