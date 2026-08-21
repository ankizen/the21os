from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.db.base import get_db

router = APIRouter(prefix="/api/system", tags=["system"])


async def check_db(db: AsyncSession) -> bool:
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    db_ok = await check_db(db)
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "unreachable",
    }
