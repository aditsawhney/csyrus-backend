import uuid
from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import RequestStatus, ReviewActionType
from app.models.request import ApprovalRequest
from app.repositories.request_repository import RequestRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewActionCreate


class ReviewerService:
    def __init__(self, db: Session):
        self.requests = RequestRepository(db)
        self.reviews = ReviewRepository(db)

    def list_assigned_requests(self, reviewer_id: uuid.UUID) -> List[ApprovalRequest]:
        return self.requests.list_for_reviewer(reviewer_id)

    def _get_actionable_request(self, *, request_id: uuid.UUID, reviewer_id: uuid.UUID) -> ApprovalRequest:
        request = self.requests.get_by_id(request_id)
        if request is None:
            raise NotFoundError("Request not found")
        if request.reviewer_id != reviewer_id:
            raise ForbiddenError("You are not the assigned reviewer for this request")
        if request.status != RequestStatus.PENDING:
            raise ConflictError("This request has already been reviewed")
        return request

    def approve(
        self, *, request_id: uuid.UUID, reviewer_id: uuid.UUID, payload: ReviewActionCreate
    ) -> ApprovalRequest:
        request = self._get_actionable_request(request_id=request_id, reviewer_id=reviewer_id)
        self.reviews.create(
            request_id=request.id,
            action=ReviewActionType.APPROVED,
            comments=payload.comments,
            reviewed_by=reviewer_id,
        )
        return self.requests.update(request, status=RequestStatus.APPROVED)

    def reject(
        self, *, request_id: uuid.UUID, reviewer_id: uuid.UUID, payload: ReviewActionCreate
    ) -> ApprovalRequest:
        request = self._get_actionable_request(request_id=request_id, reviewer_id=reviewer_id)
        self.reviews.create(
            request_id=request.id,
            action=ReviewActionType.REJECTED,
            comments=payload.comments,
            reviewed_by=reviewer_id,
        )
        return self.requests.update(request, status=RequestStatus.REJECTED)
