import os
from typing import List, Union

import msal
from msal_extensions import (
    build_encrypted_persistence,
    PersistedTokenCache,
    # PersistenceDecryptionError
)

_token_location = "token_cache.bin"


def set_token_location(location: str):
    global _token_location

    if isinstance(location, str):
        if len(location) > 5:
            _token_location = location
        else:
            raise ValueError(f"Invalid location string {location}")
    else:
        raise TypeError("Input location shall be a string.")


def get_login_name() -> Union[str, None]:
    """Get login name of current user.

    Returns:
        Union[str, None]: Login name or None
    """
    env_names = ["LOGNAME", "USER", "LNAME", "USERNAME"]
    for name in env_names:
        if os.getenv(name) is not None:
            return os.getenv(name)


def get_app_with_cache(client_id, authority: str, token_location: str = ""):
    """Get msal PublicClientApplication to authenticate against, with cached token if available.

    Args:
        client_id (str): Azure Client ID to request token from.
        authority (str): Authority to authenticate against. Should be like f"https://login.microsoftonline.com/{tenantID}".
        token_location (str, optional): Location of token persistance file.
                Defaults to "" which uses previously set value or "token_cache.bin" if not yet set. it has not been set at all, it will .

    Returns:
        msal.PublicClientApplication: Application object to authenticate with.
    """

    if isinstance(token_location, str) and len(token_location) > 0:
        set_token_location(token_location)
    else:
        # if verbose:
        # Uses default token location
        pass

    persistence = build_encrypted_persistence(_token_location)

    cache = PersistedTokenCache(persistence)
    return msal.PublicClientApplication(
        client_id=client_id, authority=authority, token_cache=cache
    )


def get_tenant_authority(tenant_id: str) -> str:
    """Get url to default authority to authenticate against.

    Args:
        tenant_id (str): Tenant ID.

    Returns:
        str: Authority url.
    """
    return f"https://login.microsoftonline.com/{tenant_id}"


class BearerAuth:
    """Class for getting bearer token authentication using msal.

    Get BearerAuth object by calling get_bearer_token.
    """

    def __init__(self, token):
        if isinstance(token, dict) and "access_result" in token:
            token = token["access_result"]

        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

    @staticmethod
    def get_auth(
        tenantID: str,
        clientID: str,
        scopes: List[str],
        username: str = "",
        token_location: str = "",
        authority: str = "",
        verbose: bool = False,
    ):
        """Get BearerAuth object interactively with access token for an azure application.

        Args:
            tenantID (str): Azure tenant ID.
            clientID (str): Azure app client ID to request token from.
            scopes (List[str]): Scopes to get token for.
            username (str, optional): User name to authenticate. Defaults to "".".
            authority (str, optional): Authenticator. Defaults to "", which converts to f"https://login.microsoftonline.com/{tenantID}".
            verbose (bool, optional): Set true to print messages. Defaults to False.

        Raises:
            Exception: Raises exception if not able to get token.

        Returns:
            BearerAuth: Token bearing authenticator object.
        """
        if authority is None or (isinstance(authority, str) and len(authority) == 0):
            authority = get_tenant_authority(tenant_id=tenantID)

        result = None
        accounts = None

        try:
            # Try to get Access Token silently from cache
            app = get_app_with_cache(
                client_id=clientID, authority=authority, token_location=token_location
            )
            accounts = app.get_accounts(username=username)
        except Exception as ex:
            # PersistenceDecryptionError
            if os.path.isfile(_token_location):
                if verbose:
                    print(
                        f"Failed getting accounts from app with cache. Attempts to delete cache-file at {_token_location}"
                    )
                os.remove(_token_location)
            app = get_app_with_cache(
                client_id=clientID, authority=authority, token_location=token_location
            )
            accounts = app.get_accounts(username=username)

        if accounts:
            if verbose:
                print(f"Found account in token cache: {username}")
                print("Attempting to obtain a new Access Token using the Refresh Token")
            result = app.acquire_token_silent(scopes=scopes, account=accounts[0])

        if result is None or (
            isinstance(result, dict)
            and "error_codes" in result.keys()
            and 50173 in result["error_codes"]
        ):
            # Try to get a new Access Token using the Interactive Flow
            if verbose:
                print(
                    "Interactive Authentication required to obtain a new Access Token."
                )
            result = app.acquire_token_interactive(scopes=scopes, domain_hint=tenantID)

        if (
            result
            and isinstance(result, dict)
            and "access_token" in result.keys()
            and result["access_token"]
        ):
            if verbose:
                print("Success")
            return BearerAuth(result["access_token"])

        if verbose:
            print(f"Failed, returned:\n{result}")
        raise Exception("Failed authenticating")
