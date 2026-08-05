"""Partner portal authentication client (service: sa-partners-api).

Thin domain subclass — only the endpoints are partner-specific; the login
mechanics + response models live in ``api_clients/auth_base.py`` (shared).
"""

from api_clients.auth_base import BaseAuthClient, LoginResponse, UserInfo

__all__ = ["PartnerAuthClient", "LoginResponse", "UserInfo"]


class PartnerAuthClient(BaseAuthClient):
    """Authentication client for the partner portal domain (sa-partners-api)."""

    LOGIN_PATH = "/sa-partners-api/v1/partner/auth/login"
    # 2FA: partner accounts can enrol TOTP; login then returns mfaRequired + a
    # challengeToken, and the code is verified here (base flow generates it via pyotp).
    MFA_VERIFY_PATH = "/sa-partners-api/v1/partner/auth/mfa/verify"
    # ME_PATH: partner "current user" endpoint not verified yet — set it (e.g.
    # "/sa-partners-api/v1/partner/auth/me") once a partner test needs me().
    ME_PATH = ""
