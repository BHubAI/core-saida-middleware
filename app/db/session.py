from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


def get_engine() -> Engine:
    engine = create_engine(
        settings.postgres_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    return engine


def get_session_maker() -> sessionmaker:
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def add_postgresql_extension() -> None:
    SessionLocal = get_session_maker()
    session = SessionLocal()
    try:
        query = text("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        session.execute(query)
        session.commit()
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    SessionLocal = get_session_maker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
