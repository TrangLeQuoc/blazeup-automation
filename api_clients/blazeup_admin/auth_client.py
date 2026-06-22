"""SA admin authentication client (service: sa-auth-api).

Thin domain subclass — only the endpoints are admin-specific; the login mechanics
+ response models live in ``api_clients/auth_base.py`` (shared). ``LoginResponse``
and ``UserInfo`` are re-exported for back-compat with existing imports.
"""

from api_clients.auth_base import BaseAuthClient, LoginResponse, UserInfo

__all__ = ["AuthClient", "LoginResponse", "UserInfo"]


class AuthClient(BaseAuthClient):
    """Authentication client for the SA admin domain (sa-auth-api)."""

    LOGIN_PATH = "/sa-auth-api/sign-in/credentials"
    ME_PATH = "/sa-auth-api/current-user"
