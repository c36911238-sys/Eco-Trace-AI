from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """
    Modern SQLAlchemy 2.0 declarative base using the class-based approach.
    All ORM models must subclass this.
    """
    pass


engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DB_ECHO,
    future=True,
    connect_args=(
        {"check_same_thread": False}
        if "sqlite" in settings.SQLALCHEMY_DATABASE_URI
        else {}
    ),
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    """
    FastAPI dependency that yields an async database session and
    guarantees it is closed after the request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session
