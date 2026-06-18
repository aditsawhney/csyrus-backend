import secrets

from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserOut
from app.services.auth_service import AuthService, build_google_login_url, exchange_code_for_profile

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.get("/google/login")
async def google_login():
    state = secrets.token_urlsafe(16)
    return RedirectResponse(build_google_login_url(state))


@router.get("/google/callback")
async def google_callback(code: str, response: Response, db: Session = Depends(get_db)):
    profile = await exchange_code_for_profile(code)

    service = AuthService(UserRepository(db))
    user = service.upsert_user_from_google_profile(profile)
    token = service.issue_session_token(user)

    redirect = RedirectResponse(url=settings.frontend_url)
    redirect.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return redirect


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
