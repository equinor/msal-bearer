import os
from typing import List, Union

import msal
import msal.exceptions
from msal_extensions import (
    build_encrypted_persistence,
    FilePersistence,
    PersistedTokenCache,
)

_token_location = "token_cache.bin"
_username = ""


def get_token(tenant_id: str, client_id: str, scopes: List[str]) -> str:
    """Get token for specified scopes for specified public Azure app registration.
    Args:
        tenant_id (str): Azure tenant ID.
        client_id (str): Public Azure app client ID to request token from.
        scopes (List[str]): Scopes to get token for.
    Returns:
        str: Token as string
    """
    b = BearerAuth.get_auth(tenantID=tenant_id, clientID=client_id, scopes=scopes)
    return b.token


def set_token_location(location: str):
    """Set location of token cache

    Args:
        location (str): Location of token cache file.

    Raises:
        ValueError: Raised if input location is not a valid location string.
        TypeError: Raised if input location is not a string.
    """
    global _token_location

    if isinstance(location, str):
        if len(location) > 4 and "." in location:
            _token_location = location
        else:
            raise ValueError(f"Invalid location string {location}")
    else:
        raise TypeError("Input location shall be a string.")


def get_token_location() -> str:
    """Getter for token location.

    Returns:
        str: Token location (pathlike)
    """
    return _token_location


def set_user_name(username: str):
    """Set user name.

    Args:
        username (str): User name to use for user_impersonation
    """
    global _username
    _username = username


def get_user_name() -> Union[str, None]:
    """Get user name if set using set_user_name or return result from get_login_name()

    Returns:
        Union[str, None]: User name
    """
    if not _username:
        return get_login_name()

    return _username


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
                Defaults to "" which uses previously set value or "token_cache.bin" if not yet set.

    Returns:
        msal.PublicClientApplication: Application object to authenticate with.
    """

    if isinstance(token_location, str) and len(token_location) > 0:
        set_token_location(token_location)
    else:
        # if verbose:
        # Uses default token location
        pass

    try:
        persistence = build_encrypted_persistence(get_token_location())
    except ImportError:
        # Handle linux case of missing gi library
        persistence = FilePersistence(get_token_location())
    except RuntimeError:
        # Handle linux case of missing gi library
        persistence = FilePersistence(get_token_location())

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

    Get BearerAuth object by calling get_auth.
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
    ) -> "BearerAuth":
        """Get BearerAuth object interactively with access token for an azure application.

        Args:
            tenantID (str): Azure tenant ID.
            clientID (str): Public Azure app client ID to request token from.
            scopes (List[str]): Scopes to get token for.
            username (str, optional): User name to authenticate. Defaults to "", which result in first account of app to be selected.".
            token_location (str, optional): Path to token cache. Defaults to "", which will call get_token_location().
            authority (str, optional): Authenticator. Defaults to "", which converts to f"https://login.microsoftonline.com/{tenantID}".
            verbose (bool, optional): Set true to print messages. Defaults to False.

        Raises:
            Exception: Raises exception if unable to get token.

        Returns:
            BearerAuth: Token bearing authenticator object.
        """
        if authority is None or (isinstance(authority, str) and len(authority) == 0):
            authority = get_tenant_authority(tenant_id=tenantID)

        result = None
        accounts = None

        try:
            if not token_location:
                token_location = get_token_location()

            # Try to get Access Token silently from cache
            app = get_app_with_cache(
                client_id=clientID, authority=authority, token_location=token_location
            )
            accounts = app.get_accounts(username=username)
        except Exception:
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
