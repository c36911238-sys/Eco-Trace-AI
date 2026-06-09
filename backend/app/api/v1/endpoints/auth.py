import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import security
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import Token, UserCreate, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> User:
    """
    Create a new user account. Validates password strength (min 8 chars,
    upper/lower/digit required) and rejects duplicate email addresses.
    """
    result = await db.execute(select(User).filter(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    db_user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    logger.info("New user registered: %s (id=%s)", db_user.email, db_user.id)
    return db_user


@router.post(
    "/login/access-token",
    response_model=Token,
    summary="Authenticate and obtain a JWT Bearer token",
)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict:
    """
    OAuth2 password flow endpoint. Accepts username (email) and password,
    returns a signed JWT access token on success.
    """
    result = await db.execute(
        select(User).filter(User.email == form_data.username)
    )
    user: User | None = result.scalars().first()

    if not user or not security.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )

    logger.info("User authenticated: %s (id=%s)", user.email, user.id)
    return {"access_token": access_token, "token_type": "bearer"}
