from sqlalchemy.orm import Session

from app.models.review import ReviewAction


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> ReviewAction:
        action = ReviewAction(**kwargs)
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action
