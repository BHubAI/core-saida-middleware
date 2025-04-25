import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import get_session
from app.models.base import BaseModel


def create_test_database():
    # Connect to default postgres database to create test database
    default_db_url = settings.postgres_url.replace(settings.POSTGRES_DB, "postgres")
    engine = create_engine(default_db_url)

    # Create test database if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("COMMIT"))  # Close any open transaction
        try:
            conn.execute(text("CREATE DATABASE test_db"))
            print("Created test database 'test_db'")
        except Exception as e:
            if "already exists" not in str(e):
                raise e
            print("Test database 'test_db' already exists")
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def create_db():
    create_test_database()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    # Create PostgreSQL test database engine
    test_db_url = settings.postgres_url.replace(settings.POSTGRES_DB, "test_db")
    engine = create_engine(
        test_db_url,
        echo=settings.DEBUG,
        future=True,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    print("Creating tables...")
    # Create all tables
    BaseModel.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        print("Dropping tables...")
        # Drop all tables after test
        BaseModel.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_get_session(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_session] = override_get_db
