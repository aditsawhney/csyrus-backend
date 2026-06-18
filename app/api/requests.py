import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.request import RequestCreate, RequestOut, RequestUpdate
from app.schemas.user import UserOut
from app.services.request_service import RequestService

router = APIRouter(prefix="/requests", tags=["requests"])


def get_service(db: Session = Depends(get_db)) -> RequestService:
    return RequestService(db)


# NOTE: declared before "/{request_id}" so it isn't swallowed by the
# dynamic route - FastAPI matches routes in declaration order.
@router.get("/reviewers", response_model=List[UserOut])
def list_reviewers(
    current_user: User = Depends(require_role(UserRole.REQUESTER)),
    service: RequestService = Depends(get_service),
):
    return service.list_reviewers()


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: RequestCreate,
    current_user: User = Depends(require_role(UserRole.REQUESTER)),
    service: RequestService = Depends(get_service),
):
    return service.create_request(requester_id=current_user.id, payload=payload)


@router.get("", response_model=List[RequestOut])
def list_my_requests(
    current_user: User = Depends(require_role(UserRole.REQUESTER)),
    service: RequestService = Depends(get_service),
):
    return service.list_my_requests(current_user.id)


@router.get("/{request_id}", response_model=RequestOut)
def get_request(
    request_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.REQUESTER)),
    service: RequestService = Depends(get_service),
):
    return service.get_owned_request(request_id=request_id, requester_id=current_user.id)


@router.put("/{request_id}", response_model=RequestOut)
def update_request(
    request_id: uuid.UUID,
    payload: RequestUpdate,
    current_user: User = Depends(require_role(UserRole.REQUESTER)),
    service: RequestService = Depends(get_service),
):
    return service.update_request(request_id=request_id, requester_id=current_user.id, payload=payload)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.REQUESTER)),
    service: RequestService = Depends(get_service),
):
    service.delete_request(request_id=request_id, requester_id=current_user.id)
