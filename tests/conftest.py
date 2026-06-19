import os
import uuid
from datetime import datetime

# Force a throwaway SQLite config before any app module reads settings,
# so tests never touch the real Postgres database or real Google
# credentials configured in .env.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database.database import Base, get_db
from app.models.enums import UserRole
from app.models.user import User
from main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_user(db_session):
    def _make_user(role: UserRole, name="Test User", email=None, google_id=None):
        email = email or f"{uuid.uuid4()}@example.com"
        google_id = google_id or str(uuid.uuid4())
        user = User(name=name, email=email, google_id=google_id, role=role, created_at=datetime.utcnow())
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def auth_headers():
    def _headers(user):
        token = create_access_token(user_id=user.id, role=user.role.value)
        return {"Authorization": f"Bearer {token}"}

    return _headers
