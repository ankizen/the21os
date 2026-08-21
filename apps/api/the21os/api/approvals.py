import uuid
from datetime import UTC, datetime

from facebook_business.exceptions import FacebookRequestError
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.audit.service import write_audit_log
from the21os.auth.dependencies import get_current_user
from the21os.db.base import get_db
from the21os.db.models import ApprovalRequest, ApprovalStatus, User
from the21os.safety import executors

router = APIRouter(prefix="/api/approvals", tags=["approvals"], dependencies=[Depends(get_current_user)])


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    action: str
    entity: str | None
    entity_id: str | None
    summary: str
    status: ApprovalStatus
    requested_by: str
    decided_at: datetime | None
    decided_by: str | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ApprovalResponse])
async def list_approvals(
    status_filter: ApprovalStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[ApprovalRequest]:
    query = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
    if status_filter is not None:
        query = query.where(ApprovalRequest.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
async def approve(
    approval_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalRequest:
    approval = await db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Already {approval.status.value.lower()}")

    request_id = str(uuid.uuid4())
    try:
        result = await executors.execute(approval.action, approval.params_json)
    except FacebookRequestError as e:
        await write_audit_log(
            db,
            request_id=request_id,
            actor=user.email,
            source="rest_api",
            action=approval.action,
            entity=approval.entity,
            entity_id=approval.entity_id,
            params=approval.params_json,
            success=False,
            decision_reason=f"Approved but Meta rejected it: {e.api_error_message() or e}",
        )
        raise HTTPException(status_code=502, detail=e.api_error_message() or "Meta API request failed") from e

    approval.status = ApprovalStatus.APPROVED
    approval.decided_at = datetime.now(UTC)
    approval.decided_by = user.email
    await db.commit()

    await write_audit_log(
        db,
        request_id=request_id,
        actor=user.email,
        source="rest_api",
        action=approval.action,
        entity=approval.entity,
        entity_id=result.get("id", approval.entity_id),
        params=approval.params_json,
        before=approval.before_json,
        after=result,
        success=True,
        decision_reason=f"Approved by {user.email}",
    )
    await db.refresh(approval)
    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
async def reject(
    approval_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalRequest:
    approval = await db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Already {approval.status.value.lower()}")

    approval.status = ApprovalStatus.REJECTED
    approval.decided_at = datetime.now(UTC)
    approval.decided_by = user.email
    await db.commit()

    await write_audit_log(
        db,
        request_id=str(uuid.uuid4()),
        actor=user.email,
        source="rest_api",
        action=approval.action,
        entity=approval.entity,
        entity_id=approval.entity_id,
        params=approval.params_json,
        success=True,
        decision_reason=f"Rejected by {user.email}",
    )
    await db.refresh(approval)
    return approval
