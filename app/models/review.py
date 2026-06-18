import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database.database import Base
from app.database.types import GUID
from app.models.enums import ReviewActionType


class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    request_id = Column(GUID(), ForeignKey("approval_requests.id"), nullable=False)
    action = Column(Enum(ReviewActionType), nullable=False)
    comments = Column(Text, nullable=True)
    reviewed_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    reviewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    request = relationship("ApprovalRequest", back_populates="review_actions")
    reviewer = relationship("User")
