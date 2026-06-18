from unittest.mock import AsyncMock, patch

from app.models.enums import UserRole


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, make_user, auth_headers):
    user = make_user(UserRole.REQUESTER, name="Adit Sawhney")
    response = client.get("/auth/me", headers=auth_headers(user))
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_google_callback_creates_new_user(client):
    fake_profile = {"sub": "google-123", "email": "new.user@example.com", "name": "New User"}
    with patch("app.api.auth.exchange_code_for_profile", new=AsyncMock(return_value=fake_profile)):
        response = client.get("/auth/google/callback", params={"code": "fake-code"}, follow_redirects=False)

    assert response.status_code in (302, 307)
    assert "csyrus_session" in response.cookies


def test_google_callback_reuses_existing_user_instead_of_duplicating(client, make_user, db_session):
    existing = make_user(UserRole.REQUESTER, email="existing@example.com", google_id="google-456")
    fake_profile = {"sub": "google-456", "email": "existing@example.com", "name": existing.name}

    with patch("app.api.auth.exchange_code_for_profile", new=AsyncMock(return_value=fake_profile)):
        response = client.get("/auth/google/callback", params={"code": "fake-code"}, follow_redirects=False)

    assert response.status_code in (302, 307)

    from app.models.user import User as UserModel
    assert db_session.query(UserModel).filter(UserModel.google_id == "google-456").count() == 1
