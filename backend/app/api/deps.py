from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.database import get_db
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    FastAPI dependency that decodes and validates the incoming JWT Bearer token,
    then fetches and returns the corresponding user from the database.

    Raises:
        HTTPException 401: If the token is missing, expired, malformed, or
                           if the user does not exist in the database.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        raw_subject: str | None = payload.get("sub")
        if raw_subject is None:
            raise _CREDENTIALS_EXCEPTION
        user_id = int(raw_subject)
    except (JWTError, ValueError):
        raise _CREDENTIALS_EXCEPTION

    result = await db.execute(select(User).filter(User.id == user_id))
    user: User | None = result.scalars().first()

    if user is None:
        raise _CREDENTIALS_EXCEPTION

    return user
