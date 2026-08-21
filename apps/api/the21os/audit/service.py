import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from the21os.audit.redact import redact
from the21os.db.models import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    request_id: str,
    actor: str,
    source: str,
    action: str,
    success: bool,
    entity: str | None = None,
    entity_id: str | None = None,
    params: dict | None = None,
    before: dict | None = None,
    after: dict | None = None,
    decision_reason: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        id=uuid.uuid4(),
        request_id=request_id,
        actor=actor,
        source=source,
        action=action,
        entity=entity,
        entity_id=entity_id,
        params_json=redact(params) if params is not None else None,
        before_json=redact(before) if before is not None else None,
        after_json=redact(after) if after is not None else None,
        decision_reason=decision_reason,
        success=success,
    )
    db.add(entry)
    await db.commit()
    return entry
