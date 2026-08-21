from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.auth.dependencies import get_current_user
from the21os.command_center.service import ask
from the21os.config import get_settings
from the21os.db.base import get_db
from the21os.db.models import User

router = APIRouter(
    prefix="/api/command-center", tags=["command-center"], dependencies=[Depends(get_current_user)]
)


class StatusResponse(BaseModel):
    configured: bool


@router.get("/status", response_model=StatusResponse)
async def command_center_status() -> StatusResponse:
    return StatusResponse(configured=get_settings().anthropic_api_key is not None)


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
    return AskResponse(**result)
