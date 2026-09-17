from typing import Optional, Protocol

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from ..config import settings

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"


class OAuthVerifier(Protocol):
    async def verify(self, id_token: str) -> str:
        """Returns the verified email address, or raises on an invalid token."""
        ...


class GoogleOAuthVerifier:
    def __init__(self, client_id: str):
        self._client_id = client_id

    async def verify(self, id_token: str) -> str:
        info = google_id_token.verify_oauth2_token(id_token, google_requests.Request(), self._client_id)
        return info["email"]


class AppleOAuthVerifier:
    def __init__(self, bundle_id: str):
        self._bundle_id = bundle_id
        self._jwks_client = jwt.PyJWKClient(APPLE_JWKS_URL)

    async def verify(self, id_token: str) -> str:
        signing_key = self._jwks_client.get_signing_key_from_jwt(id_token)
        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self._bundle_id,
            issuer="https://appleid.apple.com",
        )
        return payload["email"]


class FakeOAuthVerifier:
    """Test/dev double: the id_token IS the email, unless it's the literal string 'invalid'."""

    async def verify(self, id_token: str) -> str:
        if id_token == "invalid":
            raise ValueError("invalid token")
        return id_token


_verifiers: dict[str, OAuthVerifier] = {}
_built = False


def _build_verifiers() -> dict[str, OAuthVerifier]:
    verifiers: dict[str, OAuthVerifier] = {}

    if settings.google_oauth_client_id:
        verifiers["google"] = GoogleOAuthVerifier(settings.google_oauth_client_id)
    elif settings.environment != "production":
        verifiers["google"] = FakeOAuthVerifier()

    if settings.apple_oauth_bundle_id:
        verifiers["apple"] = AppleOAuthVerifier(settings.apple_oauth_bundle_id)
    elif settings.environment != "production":
        verifiers["apple"] = FakeOAuthVerifier()

    return verifiers


def get_oauth_verifier(provider: str) -> Optional[OAuthVerifier]:
    global _verifiers, _built
    if not _built:
        _verifiers = _build_verifiers()
        _built = True
    return _verifiers.get(provider)


def reset_oauth_verifier_cache() -> None:
    """Test helper: force the next get_oauth_verifier() call to rebuild from current settings."""
    global _verifiers, _built
    _verifiers = {}
    _built = False
