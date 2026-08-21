import uuid

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.auth.security import SESSION_COOKIE_NAME, read_session_token
from the21os.db.base import get_db
from the21os.db.models import User


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if session_token is None:
        raise unauthorized
    user_id = read_session_token(session_token)
    if user_id is None:
        raise unauthorized
    try:
        user = await db.get(User, uuid.UUID(user_id))
    except ValueError:
        raise unauthorized from None
    if user is None:
        raise unauthorized
    return user
