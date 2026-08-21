import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from the21secrets.audit.service import write_audit_log
from the21secrets.auth.dependencies import get_current_user
from the21secrets.db.base import get_db
from the21secrets.db.models import OperationalMode, SystemSettings, User

router = APIRouter(prefix="/api/system", tags=["settings"])


class SystemSettingsResponse(BaseModel):
    operational_mode: OperationalMode
    max_daily_spend_cents: int
    max_campaign_budget_cents: int
    max_budget_increase_pct: int
    max_new_campaigns_per_day: int
    max_ads_per_campaign: int
    require_approval_over_cents: int

    model_config = {"from_attributes": True}


class SystemSettingsUpdate(BaseModel):
    operational_mode: OperationalMode | None = None
    max_daily_spend_cents: int | None = None
    max_campaign_budget_cents: int | None = None
    max_budget_increase_pct: int | None = None
    max_new_campaigns_per_day: int | None = None
    max_ads_per_campaign: int | None = None
    require_approval_over_cents: int | None = None


async def _get_or_create_settings(db: AsyncSession) -> SystemSettings:
    settings = await db.get(SystemSettings, 1)
    if settings is None:
        settings = SystemSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("/settings", response_model=SystemSettingsResponse)
async def get_settings_(
    db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)
) -> SystemSettings:
    return await _get_or_create_settings(db)


@router.put("/settings", response_model=SystemSettingsResponse)
async def update_settings(
    body: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SystemSettings:
    settings = await _get_or_create_settings(db)
    before = SystemSettingsResponse.model_validate(settings).model_dump(mode="json")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(settings, field, value)
    await db.commit()
    await db.refresh(settings)

    after = SystemSettingsResponse.model_validate(settings).model_dump(mode="json")
    await write_audit_log(
        db,
        request_id=str(uuid.uuid4()),
        actor=user.email,
        source="rest_api",
        action="settings.update",
        entity="system_settings",
        entity_id="1",
        before=before,
        after=after,
        success=True,
    )
    return settings
