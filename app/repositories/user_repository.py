import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_google_id(self, google_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.google_id == google_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def list_reviewers(self) -> List[User]:
        return self.db.query(User).filter(User.role == UserRole.REVIEWER).all()

    def create(self, *, name: str, email: str, google_id: str, role: UserRole) -> User:
        user = User(name=name, email=email, google_id=google_id, role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
