"""The single path every Meta write goes through, regardless of caller
(REST API today; MCP and the Command Center in later phases will call the
same run_write — the safety gate must be identical no matter who's asking).

    validate (caller/Pydantic)
        -> hard ceilings (checks.py — never bypassed by mode)
        -> operational-mode branch (READ_ONLY / DRY_RUN / SUPERVISED / AUTONOMOUS)
        -> execute now, or queue an ApprovalRequest
        -> audit log either way
"""

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from the21os.audit.service import write_audit_log
from the21os.db.models import ApprovalRequest, OperationalMode, SystemSettings
from the21os.meta import ads, insights
from the21os.safety import checks, executors
from the21os.safety.checks import SafetyViolation


@dataclass
class WriteRequest:
    action: str
    entity: str
    entity_id: str | None
    summary: str
    params: dict
    actor: str
    source: str
    budget_cents: int | None = None
    previous_budget_cents: int | None = None
    is_new_campaign: bool = False
    is_spend_increasing: bool = False
    # Set to the target campaign_id when creating an ad, to check
    # max_ads_per_campaign. None for everything else.
    new_ad_campaign_id: str | None = None
    # Snapshot of the entity's state before this write, for the rollback
    # journal (safety/rollback.py). None for creates — there's no "before".
    before: dict | None = None


@dataclass
class WriteOutcome:
    status: Literal["executed", "dry_run", "pending_approval", "rejected"]
    result: dict | None = None
    approval_id: str | None = None
    reason: str | None = None


async def _get_settings(db: AsyncSession) -> SystemSettings:
    settings = await db.get(SystemSettings, 1)
    if settings is None:
        settings = SystemSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


async def _run_hard_ceilings(db: AsyncSession, req: WriteRequest, settings: SystemSettings) -> None:
    """Raises SafetyViolation on any breach. Order matters only for which
    message the caller sees first — all are checked regardless."""
    if req.budget_cents is not None:
        checks.check_budget_ceiling(req.budget_cents, settings)
        if req.previous_budget_cents is not None:
            checks.check_budget_increase(req.budget_cents, req.previous_budget_cents, settings)

    if req.is_new_campaign:
        await checks.check_new_campaign_quota(db, settings)

    if req.new_ad_campaign_id:
        current_count = await ads.count_ads_in_campaign(req.new_ad_campaign_id)
        checks.check_max_ads_per_campaign(current_count, settings)

    if req.is_spend_increasing:
        today = await insights.get_account_insights(date_preset="today")
        checks.check_daily_spend_ceiling(round(today.spend * 100), settings)


async def run_write(db: AsyncSession, req: WriteRequest) -> WriteOutcome:
    request_id = str(uuid.uuid4())
    settings = await _get_settings(db)

    try:
        await _run_hard_ceilings(db, req, settings)
    except SafetyViolation as e:
        await write_audit_log(
            db,
            request_id=request_id,
            actor=req.actor,
            source=req.source,
            action=req.action,
            entity=req.entity,
            entity_id=req.entity_id,
            params=req.params,
            success=False,
            decision_reason=str(e),
        )
        return WriteOutcome(status="rejected", reason=str(e))

    if settings.operational_mode == OperationalMode.READ_ONLY:
        reason = "READ_ONLY mode — writes are disabled (see Rules)."
        await write_audit_log(
            db,
            request_id=request_id,
            actor=req.actor,
            source=req.source,
            action=req.action,
            entity=req.entity,
            entity_id=req.entity_id,
            params=req.params,
            success=False,
            decision_reason=reason,
        )
        return WriteOutcome(status="rejected", reason=reason)

    if settings.operational_mode == OperationalMode.DRY_RUN:
        await write_audit_log(
            db,
            request_id=request_id,
            actor=req.actor,
            source=req.source,
            action=req.action,
            entity=req.entity,
            entity_id=req.entity_id,
            params=req.params,
            success=True,
            decision_reason="DRY_RUN — validated, not sent to Meta.",
        )
        return WriteOutcome(status="dry_run", result=req.params)

    needs_approval = settings.operational_mode == OperationalMode.SUPERVISED or (
        settings.operational_mode == OperationalMode.AUTONOMOUS
        and checks.requires_approval(req.budget_cents, settings)
    )

    if needs_approval:
        approval = ApprovalRequest(
            id=uuid.uuid4(),
            action=req.action,
            entity=req.entity,
            entity_id=req.entity_id,
            summary=req.summary,
            params_json=req.params,
            before_json=req.before,
            requested_by=req.actor,
        )
        db.add(approval)
        await db.commit()
        await write_audit_log(
            db,
            request_id=request_id,
            actor=req.actor,
            source=req.source,
            action=req.action,
            entity=req.entity,
            entity_id=req.entity_id,
            params=req.params,
            success=True,
            decision_reason=f"Queued for approval ({settings.operational_mode.value} mode).",
        )
        return WriteOutcome(status="pending_approval", approval_id=str(approval.id))

    return await _execute(db, req, request_id)


async def run_asset_upload(
    db: AsyncSession,
    *,
    action: str,
    actor: str,
    source: str,
    metadata: dict,
    upload_fn: Callable[[], Awaitable[dict]],
) -> WriteOutcome:
    """A lighter path for image/video uploads. These don't go through the
    full run_write pipeline: their payload can be up to hundreds of MB
    (video), which can't sit in ApprovalRequest.params_json or
    audit_log.params_json the way a small campaign/budget write can —
    `metadata` (filename, size, resulting hash/id) is what gets audited,
    never the raw bytes. Still mode-gated (READ_ONLY rejects, DRY_RUN
    previews) since uploading does create a real asset on Meta, but there's
    no approval-queue path for uploads — no budget/spend is at stake in
    creating an image or video asset by itself, only in what a campaign
    later does with it."""
    request_id = str(uuid.uuid4())
    settings = await _get_settings(db)

    if settings.operational_mode == OperationalMode.READ_ONLY:
        reason = "READ_ONLY mode — writes are disabled (see Rules)."
        await write_audit_log(
            db,
            request_id=request_id,
            actor=actor,
            source=source,
            action=action,
            params=metadata,
            success=False,
            decision_reason=reason,
        )
        return WriteOutcome(status="rejected", reason=reason)

    if settings.operational_mode == OperationalMode.DRY_RUN:
        await write_audit_log(
            db,
            request_id=request_id,
            actor=actor,
            source=source,
            action=action,
            params=metadata,
            success=True,
            decision_reason="DRY_RUN — validated, not sent to Meta.",
        )
        return WriteOutcome(status="dry_run", result=metadata)

    try:
        result = await upload_fn()
    except Exception as e:
        await write_audit_log(
            db,
            request_id=request_id,
            actor=actor,
            source=source,
            action=action,
            params=metadata,
            success=False,
            decision_reason=str(e),
        )
        raise

    await write_audit_log(
        db,
        request_id=request_id,
        actor=actor,
        source=source,
        action=action,
        params=metadata,
        after=result,
        success=True,
    )
    return WriteOutcome(status="executed", result=result)


async def _execute(db: AsyncSession, req: WriteRequest, request_id: str) -> WriteOutcome:
    try:
        result = await executors.execute(req.action, req.params)
    except Exception as e:
        await write_audit_log(
            db,
            request_id=request_id,
            actor=req.actor,
            source=req.source,
            action=req.action,
            entity=req.entity,
            entity_id=req.entity_id,
            params=req.params,
            success=False,
            decision_reason=str(e),
        )
        raise

    await write_audit_log(
        db,
        request_id=request_id,
        actor=req.actor,
        source=req.source,
        action=req.action,
        entity=req.entity,
        entity_id=result.get("id", req.entity_id),
        params=req.params,
        before=req.before,
        after=result,
        success=True,
    )
    return WriteOutcome(status="executed", result=result)
