"""
Test fixtures.

We override get_db via FastAPI's dependency_overrides and create tables
directly on the test engine before the client is constructed.

The startup event in main.py calls init_db() — we prevent it from running
against the real DB by pre-creating tables on the test engine and also
patching init_db to be a no-op inside the TestClient context.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
import app.database as app_db

# Shared in-memory engine (same connection across the test session)
TEST_DATABASE_URL = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def reset_tables():
    """Create tables before each test, drop after."""
    # Import models so they are registered with Base
    import app.models  # noqa
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db(reset_tables):
    """Yield a session on the test database."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(reset_tables):
    """
    FastAPI TestClient.
    - Overrides get_db to use the test engine.
    - Patches init_db so startup does NOT recreate tables on the real DB.
    """
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.database.init_db", lambda: None):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    app.dependency_overrides.clear()
