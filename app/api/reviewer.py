import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.request import RequestOut
from app.schemas.review import ReviewActionCreate
from app.services.reviewer_service import ReviewerService

router = APIRouter(prefix="/reviewer", tags=["reviewer"])


def get_service(db: Session = Depends(get_db)) -> ReviewerService:
    return ReviewerService(db)


@router.get("/requests", response_model=List[RequestOut])
def list_assigned_requests(
    current_user: User = Depends(require_role(UserRole.REVIEWER)),
    service: ReviewerService = Depends(get_service),
):
    return service.list_assigned_requests(current_user.id)


@router.post("/requests/{request_id}/approve", response_model=RequestOut)
def approve_request(
    request_id: uuid.UUID,
    payload: ReviewActionCreate,
    current_user: User = Depends(require_role(UserRole.REVIEWER)),
    service: ReviewerService = Depends(get_service),
):
    return service.approve(request_id=request_id, reviewer_id=current_user.id, payload=payload)


@router.post("/requests/{request_id}/reject", response_model=RequestOut)
def reject_request(
    request_id: uuid.UUID,
    payload: ReviewActionCreate,
    current_user: User = Depends(require_role(UserRole.REVIEWER)),
    service: ReviewerService = Depends(get_service),
):
    return service.reject(request_id=request_id, reviewer_id=current_user.id, payload=payload)
