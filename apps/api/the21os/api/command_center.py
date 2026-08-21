import uuid
from typing import Any

from anthropic import APIStatusError
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.audit.service import write_audit_log
from the21os.auth.dependencies import get_current_user
from the21os.command_center.service import ask
from the21os.config import get_settings
from the21os.db.base import get_db
from the21os.db.models import SystemSettings, User

router = APIRouter(
    prefix="/api/command-center", tags=["command-center"], dependencies=[Depends(get_current_user)]
)


class StatusResponse(BaseModel):
    configured: bool
    # "database" when a key was set via /key (overrides the env var),
    # "environment" when only ANTHROPIC_API_KEY is set, else None.
    source: str | None = None
    key_preview: str | None = None


async def _status(db: AsyncSession) -> StatusResponse:
    row = await db.get(SystemSettings, 1)
    db_key = row.anthropic_api_key if row else None
    env_key = get_settings().anthropic_api_key
    if db_key:
        return StatusResponse(configured=True, source="database", key_preview=f"…{db_key[-4:]}")
    if env_key:
        return StatusResponse(configured=True, source="environment")
    return StatusResponse(configured=False)


@router.get("/status", response_model=StatusResponse)
async def command_center_status(db: AsyncSession = Depends(get_db)) -> StatusResponse:
    return await _status(db)


class KeyUpdateRequest(BaseModel):
    api_key: str


@router.put("/key", response_model=StatusResponse)
async def update_api_key(
    body: KeyUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> StatusResponse:
    key = body.api_key.strip()
    if not key:
        raise HTTPException(status_code=422, detail="API key cannot be empty")

    row = await db.get(SystemSettings, 1)
    if row is None:
        row = SystemSettings(id=1)
        db.add(row)
    row.anthropic_api_key = key
    await db.commit()

    await write_audit_log(
        db,
        request_id=str(uuid.uuid4()),
        actor=user.email,
        source="rest_api",
        action="command_center.key_update",
        entity="system_settings",
        entity_id="1",
        params={"api_key": key},  # redacted automatically — key name matches the secret pattern
        success=True,
        decision_reason=f"Anthropic API key updated (ends …{key[-4:]})",
    )
    return await _status(db)


class ToolTraceEntry(BaseModel):
    tool: str
    input: dict[str, Any]
    result: dict[str, Any]


class AskRequest(BaseModel):
    # Full Anthropic Messages API conversation so far — the client keeps
    # and re-sends this each turn since there's no server-side chat store.
    messages: list[dict[str, Any]]


class AskResponse(BaseModel):
    reply: str
    trace: list[ToolTraceEntry]
    messages: list[dict[str, Any]]


@router.post("/ask", response_model=AskResponse)
async def ask_command_center(
    body: AskRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AskResponse:
    try:
        result = await ask(db, user, body.messages)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except APIStatusError as e:
        detail = e.body.get("error", {}).get("message", str(e)) if isinstance(e.body, dict) else str(e)
        raise HTTPException(status_code=502, detail=f"Claude API: {detail}") from e
    return AskResponse(**result)
