# msal-bearer
Python package to get auth token interactively for a msal public client application and cache it locally.

## Usage


````
tenantID = "YOUR_TENANT_ID"
client_id = "YOUR_CLIENT_ID"
scope = ["YOUR_SCOPE"]

auth = BearerAuth.get_bearer_token_auth(
    tenantID=tenantID,
    clientID=client_id,
    scopes=scope
)

# Supports requests
response = requests.get("https://www.example.com/", auth=auth)

# and httpx
client = httpx.Client()
response = client.get("https://www.example.com/", auth=auth)

````

THe auth object can be used as an auth for both requests and httpx.


## Installing
Install using pip or poetry from pypi.

````
pip install msal_bearer
````


## Alternatives
Other similar packages include https://pypi.org/project/msal-requests-auth/ (for confidential client applications) and https://pypi.org/project/msal-interactive-token-acquirer/ (no caching implemented).

