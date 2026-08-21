from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.auth.security import hash_password
from the21os.config import get_settings
from the21os.db.models import User


async def seed_admin_user(db: AsyncSession) -> None:
    """Create the single admin user from ADMIN_EMAIL/ADMIN_PASSWORD if the
    users table is empty. No-op after the first user exists — change the
    password through the app from then on, not by editing env vars."""
    count = await db.scalar(select(func.count()).select_from(User))
    if count:
        return
    settings = get_settings()
    db.add(User(email=settings.admin_email, password_hash=hash_password(settings.admin_password)))
    await db.commit()
