import uuid
from typing import Optional

import jwt
from fastapi import Cookie, Depends, Header
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User

settings = get_settings()


def _extract_token(authorization: Optional[str], session_cookie: Optional[str]) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    if session_cookie:
        return session_cookie
    raise UnauthorizedError("Missing authentication credentials")


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
    session_cookie: Optional[str] = Cookie(default=None, alias=settings.session_cookie_name),
) -> User:
    token = _extract_token(authorization, session_cookie)
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired session") from exc

    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise UnauthorizedError("User no longer exists")
    return user


def require_role(role: UserRole):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise ForbiddenError(f"This action requires the {role.value} role")
        return user

    return _checker
