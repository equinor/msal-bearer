# msal-bearer [![SNYK dependency check](https://github.com/equinor/msal-bearer/actions/workflows/snyk.yml/badge.svg)](https://github.com/equinor/msal-bearer/actions/workflows/snyk.yml)
Python package to get authorization token interactively for a msal public client application supporting local cache and refreshing the token.

## Usage


````
from msal_bearer import BearerAuth

tenantID = "YOUR_TENANT_ID"
client_id = "YOUR_CLIENT_ID"
scope = ["YOUR_SCOPE"]

auth = BearerAuth.get_auth(
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


## Installing
Clone and install using poetry or install from pypi using pip. 

````
pip install msal_bearer
````


## Alternatives
Other similar packages include https://pypi.org/project/msal-requests-auth/ (for confidential client applications) and https://pypi.org/project/msal-interactive-token-acquirer/ (no caching implemented).

