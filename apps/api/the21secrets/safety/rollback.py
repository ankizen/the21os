"""Rollback for the write types that are genuinely reversible: pause/resume
(trivially — flip back) and budget changes (revert to the pre-change value
captured in audit_log.before_json). Not every write is reversible — a
campaign.create can be paused but not un-created, so it's deliberately
absent from _REVERSIBLE here rather than offering a rollback that lies
about what it does (master prompt SS21: label irreversible operations
clearly, don't pretend).

A rollback is itself just another write, going through the exact same
safety pipeline — reverting a budget cut back up is an increase like any
other and can still hit the budget-increase ceiling."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from the21secrets.db.models import AuditLog
from the21secrets.safety.pipeline import WriteOutcome, WriteRequest, run_write

_ENTITY_ID_KEY = {"campaign": "campaign_id", "adset": "adset_id", "ad": "ad_id"}

_PAUSE_RESUME_INVERSE = {
    "campaign.pause": "campaign.resume",
    "campaign.resume": "campaign.pause",
    "adset.pause": "adset.resume",
    "adset.resume": "adset.pause",
    "ad.pause": "ad.resume",
    "ad.resume": "ad.pause",
}

_BUDGET_ACTIONS = {"campaign.budget_update", "adset.budget_update"}


class NotReversible(ValueError):
    pass


async def rollback(db: AsyncSession, audit_log_id: uuid.UUID, actor: str, source: str) -> WriteOutcome:
    entry = await db.get(AuditLog, audit_log_id)
    if entry is None:
        raise ValueError(f"No audit log entry {audit_log_id}")
    if not entry.success:
        raise NotReversible("Can't roll back an action that failed in the first place.")

    entity_id_key = _ENTITY_ID_KEY.get(entry.entity or "")

    if entry.action in _PAUSE_RESUME_INVERSE:
        inverse_action = _PAUSE_RESUME_INVERSE[entry.action]
        req = WriteRequest(
            action=inverse_action,
            entity=entry.entity or "",
            entity_id=entry.entity_id,
            summary=f"Rollback of {entry.action} on {entry.entity_id}",
            params=entry.params_json or {},
            actor=actor,
            source=source,
        )
        return await run_write(db, req)

    if entry.action in _BUDGET_ACTIONS and entity_id_key:
        if not entry.before_json or entry.before_json.get("daily_budget") is None:
            raise NotReversible("No prior budget was recorded for this change — can't roll back.")
        previous_budget_cents = int(entry.before_json["daily_budget"])
        current_budget_cents = int((entry.after_json or {}).get("daily_budget") or 0)
        req = WriteRequest(
            action=entry.action,
            entity=entry.entity or "",
            entity_id=entry.entity_id,
            summary=f"Rollback of {entry.action} on {entry.entity_id} to previous budget",
            params={entity_id_key: entry.entity_id, "daily_budget_cents": previous_budget_cents},
            actor=actor,
            source=source,
            budget_cents=previous_budget_cents,
            previous_budget_cents=current_budget_cents,
            before=entry.after_json,
        )
        return await run_write(db, req)

    raise NotReversible(f"{entry.action!r} isn't reversible — only pause/resume and budget changes are.")
