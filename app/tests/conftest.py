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
def engine():
    test_db_url = settings.postgres_url.replace(settings.POSTGRES_DB, "test_db")

    engine = create_engine(
        test_db_url,
        echo=settings.DEBUG,
        future=True,
    )
    with engine.connect():
        BaseModel.metadata.create_all(bind=engine)
        try:
            yield engine
        finally:
            BaseModel.metadata.drop_all(bind=engine)
            engine.dispose()


@pytest.fixture
def session_maker(engine):
    yield sessionmaker(autocommit=False, autoflush=True, expire_on_commit=False, bind=engine)


@pytest.fixture
def db_session(session_maker):
    with session_maker() as session:
        try:
            yield session
        finally:
            session.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    return TestClient(app)
