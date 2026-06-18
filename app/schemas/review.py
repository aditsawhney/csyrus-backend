import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReviewActionType


class ReviewActionCreate(BaseModel):
    comments: Optional[str] = None


class ReviewActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: uuid.UUID
    action: ReviewActionType
    comments: Optional[str]
    reviewed_by: uuid.UUID
    reviewed_at: datetime
