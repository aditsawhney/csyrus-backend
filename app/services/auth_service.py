import urllib.parse

import httpx

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository

settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def build_google_login_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_profile(code: str) -> dict:
    """Exchange an OAuth authorization code for the user's Google profile.

    Kept as a standalone function (rather than a method) so tests can
    monkeypatch just the network call without touching anything else in
    the auth flow.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            raise UnauthorizedError("Failed to exchange authorization code with Google")

        access_token = token_response.json().get("access_token")

        profile_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_response.status_code != 200:
            raise UnauthorizedError("Failed to fetch Google profile")

        return profile_response.json()


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def upsert_user_from_google_profile(self, profile: dict) -> User:
        google_id = profile.get("sub")
        email = profile.get("email")
        name = profile.get("name", email)

        if not google_id or not email:
            raise UnauthorizedError("Google did not return a complete profile")

        existing = self.user_repo.get_by_google_id(google_id)
        if existing:
            return existing

        # New accounts default to Requester. Promoting someone to Reviewer
        # is treated as an administrative action outside the OAuth flow -
        # see ENGINEERING_DECISIONS.md for the reasoning behind this.
        return self.user_repo.create(name=name, email=email, google_id=google_id, role=UserRole.REQUESTER)

    def issue_session_token(self, user: User) -> str:
        return create_access_token(user_id=user.id, role=user.role.value)
