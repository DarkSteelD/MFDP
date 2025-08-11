"""
Test configuration and fixtures for the ML Service API.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_database.db")

import pytest
import tempfile
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from faker import Faker

from src.main import app
from src.db.models import Base, User, Transaction
from src.dependencies import get_db
from src.core.security import get_password_hash, create_access_token
from src.dependencies import get_current_active_user

fake = Faker()

TEST_DATABASE_URL = "sqlite:///./test_database.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    if os.path.exists("./test_database.db"):
        os.remove("./test_database.db")

@pytest.fixture(scope="function")
def test_db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def test_client(test_db_session):
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    return {
        "email": fake.email(),
        "password": fake.password(length=12)
    }

@pytest.fixture
def test_user(test_db_session, test_user_data) -> User:
    user = User(
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        balance=100.0,
        is_admin=False,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user

@pytest.fixture
def test_admin_user(test_db_session) -> User:
    admin_user = User(
        email=fake.email(),
        hashed_password=get_password_hash("admin_password"),
        balance=1000.0,
        is_admin=True,
        is_active=True
    )
    test_db_session.add(admin_user)
    test_db_session.commit()
    test_db_session.refresh(admin_user)
    return admin_user

@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_auth_headers(test_admin_user: User) -> Dict[str, str]:
    access_token = create_access_token(data={"sub": str(test_admin_user.id)})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def test_image_base64() -> str:
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

@pytest.fixture
def test_transaction(test_db_session, test_user: User) -> Transaction:
    transaction = Transaction(
        user_id=test_user.id,
        type="deposit",
        amount=50.0,
        comment="Test deposit"
    )
    test_db_session.add(transaction)
    test_db_session.commit()
    test_db_session.refresh(transaction)
    return transaction

@pytest.fixture
def authenticated_client(test_client, test_user, auth_headers):
    def override_get_current_active_user():
        return test_user
    
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    test_client.headers.update(auth_headers)
    
    yield test_client
    
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user] 