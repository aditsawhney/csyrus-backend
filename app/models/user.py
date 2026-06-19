import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.database.types import GUID
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    google_id = Column(String(255), nullable=False, unique=True, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.REQUESTER)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    requests_created = relationship(
        "ApprovalRequest",
        back_populates="requester",
        foreign_keys="ApprovalRequest.created_by",
    )
    requests_to_review = relationship(
        "ApprovalRequest",
        back_populates="reviewer",
        foreign_keys="ApprovalRequest.reviewer_id",
    )
