import uuid
from datetime import datetime

from facebook_business.exceptions import FacebookRequestError
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.auth.dependencies import get_current_user
from the21os.db.base import get_db
from the21os.db.models import AuditLog, User
from the21os.safety.rollback import NotReversible
from the21os.safety.rollback import rollback as rollback_write

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


class RollbackResponse(BaseModel):
    status: str
    result: dict | None = None
    approval_id: str | None = None
    reason: str | None = None


@router.post("/{audit_log_id}/rollback", response_model=RollbackResponse)
async def rollback_action(
    audit_log_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RollbackResponse:
    """Reverses a pause/resume or budget change by replaying its inverse
    through the same safety pipeline — see safety/rollback.py for exactly
    which action types are reversible and why the rest aren't."""
    try:
        outcome = await rollback_write(db, audit_log_id, actor=user.email, source="rest_api")
    except NotReversible as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FacebookRequestError as e:
        raise HTTPException(status_code=502, detail=e.api_error_message() or "Meta API request failed") from e
    return RollbackResponse(
        status=outcome.status, result=outcome.result, approval_id=outcome.approval_id, reason=outcome.reason
    )
