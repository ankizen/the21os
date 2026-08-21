import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the21secrets.auth.dependencies import get_current_user
from the21secrets.db.base import get_db
from the21secrets.db.models import AuditLog, User

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    request_id: str
    actor: str
    source: str
    action: str
    entity: str | None
    entity_id: str | None
    params_json: dict | None
    before_json: dict | None
    after_json: dict | None
    decision_reason: str | None
    success: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_log(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[AuditLog]:
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    return list(result.scalars().all())
