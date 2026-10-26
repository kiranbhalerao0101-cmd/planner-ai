from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

def _make_engine():
    url = settings.database_url
    # SQLite needs check_same_thread=False; PostgreSQL does not
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    # Render gives postgres:// but SQLAlchemy 2.x needs postgresql://
    url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)

engine = _make_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import app.database as _self  # always use current module-level engine
    from . import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=_self.engine)
