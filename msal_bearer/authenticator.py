from azure.identity import DefaultAzureCredential
from typing import List, Optional, Union

from msal_bearer import BearerAuth, get_user_name
from msal import ConfidentialClientApplication


class Authenticator:
    """Class for authentication to Azure.

    Supporting three methods:
    1. Public app authentication (tenant_id, client_id must be set)
    2. Client secret authentication (client_id and client_secret must be set)
    3. Azure authentication (if no other method is possible), will cycle through DefaultAzureCredential methods with its various ways of authenticating.

    """

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        authority: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        scopes: Optional[Union[str, List[str]]] = None,
    ):
        """Initializer for Authenticator class.

        Args:
            tenant_id (Optional[str], optional): Azure tenant id. Defaults to None.
            client_id (Optional[str], optional): _description_. Defaults to None.
            client_secret (Optional[str], optional): _description_. Defaults to None.
            authority (Optional[str], optional): _description_. Defaults to None, which converts to f"https://login.microsoftonline.com/{tenant_id}".
            redirect_uri (Optional[str], optional): _description_. Defaults to None.
            scopes (Optional[Union[str, List[str]]], optional): _description_. Defaults to None.
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = authority
        self.redirect_uri = redirect_uri
        self.token = ""
        self.user_name = ""
        if scopes:
            self.set_scope(scopes)
        else:
            self.scopes = []

    def set_client_id(self, client_id: str) -> None:
        self.client_id = client_id

    def get_client_id(self) -> str:
        if not self.client_id:
            raise ValueError("Client ID is not set")
        return self.client_id

    def get_tenant_id(self) -> str:
        if not self.tenant_id:
            raise ValueError("Tenant ID is not set")
        return self.tenant_id

    def set_client_secret(self, client_secret: str) -> None:
        self.client_secret = client_secret

    def set_token(self, token: str) -> None:
        self.token = token

    def set_scope(self, scope: Union[List[str], str]) -> None:
        if isinstance(scope, str):
            scope = [scope]
        self.scopes = scope

    def get_scope(self) -> List[str]:
        if self.scopes is None or len(self.scopes) == 0:
            return [f"{self.get_client_id()}/.default"]
        return self.scopes

    def get_token(self, scopes: Optional[List[str]] = None) -> str:
        if self.token:
            return self.token

        if scopes is None:
            scopes = self.get_scope()

        if self.client_secret:
            c = ConfidentialClientApplication(
                client_id=self.get_client_id(),
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.get_tenant_id()}",
            )
            d = c.acquire_token_for_client(scopes=scopes)
            if d is None:
                raise ValueError("Could not get token.")
            if "access_token" not in d:
                raise ValueError(
                    f"Could not get token: {d.get('error_description') if 'error_description' in d else d.get('error')}"
                )
            return d["access_token"]

        if self.client_id:
            return self.get_public_app_token()

        return self.get_az_token(self.get_scope())

    def get_az_token(self, scope: Union[List[str], str]) -> str:
        """Getter for token uzing azure authentication.

        Returns:
            str: Token from azure authentication
        """
        if isinstance(scope, list):
            scope = scope[0]
        credential = DefaultAzureCredential()
        token = credential.get_token(scope, tenant_id=self.get_tenant_id())
        return token[0]

    def get_public_app_token(
        self,
        username: Optional[str] = None,
        scope: Optional[Union[List[str], str]] = None,
    ) -> str:
        if not username:
            username = self.user_name  # type: ignore
        else:
            self.user_name = username

        if username is not None:
            username = username.upper()

        auth = BearerAuth.get_auth(
            tenantID=self.get_tenant_id(),
            clientID=self.get_client_id(),
            scopes=self.get_scope(),
            username=username,
        )
        return auth.token  # type: ignore
