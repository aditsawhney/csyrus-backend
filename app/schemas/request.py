import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Priority, RequestStatus


class RequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    priority: Priority = Priority.MEDIUM
    reviewer_id: uuid.UUID


class RequestUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1)
    priority: Optional[Priority] = None
    reviewer_id: Optional[uuid.UUID] = None


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    priority: Priority
    status: RequestStatus
    created_by: uuid.UUID
    reviewer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
