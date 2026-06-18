import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.enums import RequestStatus
from app.models.request import ApprovalRequest


class RequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, request_id: uuid.UUID) -> Optional[ApprovalRequest]:
        return self.db.get(ApprovalRequest, request_id)

    def list_for_requester(self, requester_id: uuid.UUID) -> List[ApprovalRequest]:
        return (
            self.db.query(ApprovalRequest)
            .filter(ApprovalRequest.created_by == requester_id)
            .order_by(ApprovalRequest.created_at.desc())
            .all()
        )

    def list_for_reviewer(
        self, reviewer_id: uuid.UUID, status: Optional[RequestStatus] = None
    ) -> List[ApprovalRequest]:
        query = self.db.query(ApprovalRequest).filter(ApprovalRequest.reviewer_id == reviewer_id)
        if status is not None:
            query = query.filter(ApprovalRequest.status == status)
        return query.order_by(ApprovalRequest.created_at.desc()).all()

    def create(self, **kwargs) -> ApprovalRequest:
        request = ApprovalRequest(**kwargs)
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def update(self, request: ApprovalRequest, **fields) -> ApprovalRequest:
        for key, value in fields.items():
            if value is not None:
                setattr(request, key, value)
        self.db.commit()
        self.db.refresh(request)
        return request

    def delete(self, request: ApprovalRequest) -> None:
        self.db.delete(request)
        self.db.commit()
