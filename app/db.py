from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def engine():
    url = get_settings().database_url
    options = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    return create_engine(url, **options)


def get_db() -> Generator[Session, None, None]:
    with sessionmaker(bind=engine(), expire_on_commit=False)() as session:
        yield session
