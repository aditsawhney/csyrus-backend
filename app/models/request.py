import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.database.types import GUID
from app.models.enums import Priority, RequestStatus


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Enum(Priority), nullable=False, default=Priority.MEDIUM)
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING)

    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    requester = relationship("User", back_populates="requests_created", foreign_keys=[created_by])
    reviewer = relationship("User", back_populates="requests_to_review", foreign_keys=[reviewer_id])
    review_actions = relationship("ReviewAction", back_populates="request", cascade="all, delete-orphan")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    requester = relationship("User", back_populates="requests_created", foreign_keys=[created_by])
    reviewer = relationship("User", back_populates="requests_to_review", foreign_keys=[reviewer_id])
    review_actions = relationship("ReviewAction", back_populates="request", cascade="all, delete-orphan")
