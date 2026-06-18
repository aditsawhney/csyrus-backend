import uuid
from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.enums import RequestStatus, UserRole
from app.models.request import ApprovalRequest
from app.repositories.request_repository import RequestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.request import RequestCreate, RequestUpdate


class RequestService:
    def __init__(self, db: Session):
        self.requests = RequestRepository(db)
        self.users = UserRepository(db)

    def list_reviewers(self):
        return self.users.list_reviewers()

    def create_request(self, *, requester_id: uuid.UUID, payload: RequestCreate) -> ApprovalRequest:
        reviewer = self.users.get_by_id(payload.reviewer_id)
        if reviewer is None or reviewer.role != UserRole.REVIEWER:
            raise NotFoundError("Assigned reviewer was not found")

        return self.requests.create(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            created_by=requester_id,
            reviewer_id=payload.reviewer_id,
        )

    def list_my_requests(self, requester_id: uuid.UUID) -> List[ApprovalRequest]:
        return self.requests.list_for_requester(requester_id)

    def get_owned_request(self, *, request_id: uuid.UUID, requester_id: uuid.UUID) -> ApprovalRequest:
        request = self.requests.get_by_id(request_id)
        if request is None:
            raise NotFoundError("Request not found")
        if request.created_by != requester_id:
            raise ForbiddenError("You can only access your own requests")
        return request

    def update_request(
        self, *, request_id: uuid.UUID, requester_id: uuid.UUID, payload: RequestUpdate
    ) -> ApprovalRequest:
        request = self.get_owned_request(request_id=request_id, requester_id=requester_id)
        if request.status != RequestStatus.PENDING:
            raise ConflictError("Only pending requests can be edited")

        if payload.reviewer_id is not None:
            reviewer = self.users.get_by_id(payload.reviewer_id)
            if reviewer is None or reviewer.role != UserRole.REVIEWER:
                raise NotFoundError("Assigned reviewer was not found")

        return self.requests.update(
            request,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            reviewer_id=payload.reviewer_id,
        )

    def delete_request(self, *, request_id: uuid.UUID, requester_id: uuid.UUID) -> None:
        request = self.get_owned_request(request_id=request_id, requester_id=requester_id)
        if request.status != RequestStatus.PENDING:
            raise ConflictError("Only pending requests can be deleted")
        self.requests.delete(request)
