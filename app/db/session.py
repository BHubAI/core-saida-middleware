from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings


def get_engine() -> Engine:
    engine = create_engine(
        settings.POSTGRES_URL,
        echo=settings.DEBUG,
    )
    return engine


def get_session_maker() -> sessionmaker:
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)



def add_postgresql_extension() -> None:
    with get_session_maker() as db:
        query = text("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        db.execute(query)


def get_session() -> Generator[Session, None, None]:
    with get_session_maker() as session:
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
