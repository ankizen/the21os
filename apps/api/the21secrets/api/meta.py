from collections import Counter
from collections.abc import Awaitable, Callable
from typing import Literal, TypeVar

from facebook_business.exceptions import FacebookRequestError
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from the21secrets.auth.dependencies import get_current_user
from the21secrets.db.base import get_db
from the21secrets.db.models import User
from the21secrets.meta import accounts, ads, adsets, assets, campaigns, creatives, insights
from the21secrets.meta.client import MetaNotConfigured
from the21secrets.meta.models import AccountInfo, Ad, AdSet, Campaign, Creative
from the21secrets.meta.models import Insights as InsightsModel
from the21secrets.safety.pipeline import WriteRequest, run_asset_upload, run_write

router = APIRouter(prefix="/api/meta", tags=["meta"], dependencies=[Depends(get_current_user)])

T = TypeVar("T")


async def _run(fn: Callable[[], Awaitable[T]]) -> T:
    try:
        return await fn()
    except MetaNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except FacebookRequestError as e:
        raise HTTPException(status_code=502, detail=e.api_error_message() or "Meta API request failed") from e


class WriteResponse(BaseModel):
    status: Literal["executed", "dry_run", "pending_approval", "rejected"]
    result: dict | None = None
    approval_id: str | None = None
    reason: str | None = None


async def _do_write(db: AsyncSession, req: WriteRequest) -> WriteResponse:
    try:
        outcome = await run_write(db, req)
    except FacebookRequestError as e:
        raise HTTPException(status_code=502, detail=e.api_error_message() or "Meta API request failed") from e
    return WriteResponse(
        status=outcome.status, result=outcome.result, approval_id=outcome.approval_id, reason=outcome.reason
    )


# ---- reads ------------------------------------------------------------


@router.get("/account", response_model=AccountInfo)
async def get_account() -> AccountInfo:
    return await _run(accounts.get_account_info)


@router.get("/campaigns", response_model=list[Campaign])
async def get_campaigns() -> list[Campaign]:
    return await _run(campaigns.list_campaigns)


@router.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: str) -> Campaign:
    return await _run(lambda: campaigns.get_campaign(campaign_id))


@router.get("/adsets", response_model=list[AdSet])
async def get_adsets(campaign_id: str | None = Query(default=None)) -> list[AdSet]:
    return await _run(lambda: adsets.list_adsets(campaign_id=campaign_id))


@router.get("/ads", response_model=list[Ad])
async def get_ads(adset_id: str | None = Query(default=None)) -> list[Ad]:
    return await _run(lambda: ads.list_ads(adset_id=adset_id))


@router.get("/insights/account", response_model=InsightsModel)
async def get_account_insights(date_preset: str = Query(default="today")) -> InsightsModel:
    return await _run(lambda: insights.get_account_insights(date_preset=date_preset))


@router.get("/insights/campaigns", response_model=list[InsightsModel])
async def get_campaign_insights(date_preset: str = Query(default="today")) -> list[InsightsModel]:
    return await _run(lambda: insights.get_campaign_insights(date_preset=date_preset))


# ---- campaign writes ----------------------------------------------------


class CreateCampaignRequest(BaseModel):
    name: str
    objective: str
    daily_budget_cents: int


class BudgetUpdateRequest(BaseModel):
    daily_budget_cents: int


class DuplicateCampaignRequest(BaseModel):
    name_suffix: str = " (copy)"


@router.post("/campaigns", response_model=WriteResponse)
async def create_campaign(
    body: CreateCampaignRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    req = WriteRequest(
        action="campaign.create",
        entity="campaign",
        entity_id=None,
        summary=f"Create campaign '{body.name}' (₹{body.daily_budget_cents / 100:.2f}/day, starts PAUSED)",
        params=body.model_dump(),
        actor=user.email,
        source="rest_api",
        budget_cents=body.daily_budget_cents,
        is_new_campaign=True,
    )
    return await _do_write(db, req)


@router.patch("/campaigns/{campaign_id}/budget", response_model=WriteResponse)
async def update_campaign_budget(
    campaign_id: str,
    body: BudgetUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WriteResponse:
    current = await _run(lambda: campaigns.get_campaign(campaign_id))
    previous_cents = int(current.daily_budget) if current.daily_budget else 0
    req = WriteRequest(
        action="campaign.budget_update",
        entity="campaign",
        entity_id=campaign_id,
        summary=f"Update '{current.name}' daily budget to ₹{body.daily_budget_cents / 100:.2f}",
        params={"campaign_id": campaign_id, "daily_budget_cents": body.daily_budget_cents},
        actor=user.email,
        source="rest_api",
        budget_cents=body.daily_budget_cents,
        previous_budget_cents=previous_cents,
        is_spend_increasing=body.daily_budget_cents > previous_cents,
        before=current.model_dump(),
    )
    return await _do_write(db, req)


@router.post("/campaigns/{campaign_id}/pause", response_model=WriteResponse)
async def pause_campaign(
    campaign_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    current = await _run(lambda: campaigns.get_campaign(campaign_id))
    req = WriteRequest(
        action="campaign.pause",
        entity="campaign",
        entity_id=campaign_id,
        summary=f"Pause '{current.name}'",
        params={"campaign_id": campaign_id},
        actor=user.email,
        source="rest_api",
        before=current.model_dump(),
    )
    return await _do_write(db, req)


@router.post("/campaigns/{campaign_id}/resume", response_model=WriteResponse)
async def resume_campaign(
    campaign_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    current = await _run(lambda: campaigns.get_campaign(campaign_id))
    req = WriteRequest(
        action="campaign.resume",
        entity="campaign",
        entity_id=campaign_id,
        summary=f"Resume '{current.name}'",
        params={"campaign_id": campaign_id},
        actor=user.email,
        source="rest_api",
        is_spend_increasing=True,
        before=current.model_dump(),
    )
    return await _do_write(db, req)


@router.post("/campaigns/{campaign_id}/duplicate", response_model=WriteResponse)
async def duplicate_campaign(
    campaign_id: str,
    body: DuplicateCampaignRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WriteResponse:
    source = await _run(lambda: campaigns.get_campaign(campaign_id))
    budget_cents = int(source.daily_budget) if source.daily_budget else 0
    req = WriteRequest(
        action="campaign.duplicate",
        entity="campaign",
        entity_id=None,
        summary=f"Duplicate '{source.name}' (campaign shell only — no ad sets/ads/creatives)",
        params={"campaign_id": campaign_id, "name_suffix": body.name_suffix},
        actor=user.email,
        source="rest_api",
        budget_cents=budget_cents,
        is_new_campaign=True,
    )
    return await _do_write(db, req)


# ---- ad set writes --------------------------------------------------------


@router.patch("/adsets/{adset_id}/budget", response_model=WriteResponse)
async def update_adset_budget(
    adset_id: str,
    body: BudgetUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WriteResponse:
    current = await _run(lambda: adsets.get_adset(adset_id))
    previous_cents = int(current.daily_budget) if current.daily_budget else 0
    req = WriteRequest(
        action="adset.budget_update",
        entity="adset",
        entity_id=adset_id,
        summary=f"Update '{current.name}' daily budget to ₹{body.daily_budget_cents / 100:.2f}",
        params={"adset_id": adset_id, "daily_budget_cents": body.daily_budget_cents},
        actor=user.email,
        source="rest_api",
        budget_cents=body.daily_budget_cents,
        previous_budget_cents=previous_cents,
        is_spend_increasing=body.daily_budget_cents > previous_cents,
        before=current.model_dump(),
    )
    return await _do_write(db, req)


@router.post("/adsets/{adset_id}/pause", response_model=WriteResponse)
async def pause_adset(
    adset_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    current = await _run(lambda: adsets.get_adset(adset_id))
    req = WriteRequest(
        action="adset.pause",
        entity="adset",
        entity_id=adset_id,
        summary=f"Pause '{current.name}'",
        params={"adset_id": adset_id},
        actor=user.email,
        source="rest_api",
        before=current.model_dump(),
    )
    return await _do_write(db, req)


@router.post("/adsets/{adset_id}/resume", response_model=WriteResponse)
async def resume_adset(
    adset_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    current = await _run(lambda: adsets.get_adset(adset_id))
    req = WriteRequest(
        action="adset.resume",
        entity="adset",
        entity_id=adset_id,
        summary=f"Resume '{current.name}'",
        params={"adset_id": adset_id},
        actor=user.email,
        source="rest_api",
        is_spend_increasing=True,
        before=current.model_dump(),
    )
    return await _do_write(db, req)


# ---- ad writes -------------------------------------------------------------


@router.post("/ads/{ad_id}/pause", response_model=WriteResponse)
async def pause_ad(
    ad_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    current = await _run(lambda: ads.get_ad(ad_id))
    req = WriteRequest(
        action="ad.pause",
        entity="ad",
        entity_id=ad_id,
        summary=f"Pause '{current.name}'",
        params={"ad_id": ad_id},
        actor=user.email,
        source="rest_api",
        before=current.model_dump(),
    )
    return await _do_write(db, req)


@router.post("/ads/{ad_id}/resume", response_model=WriteResponse)
async def resume_ad(
    ad_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    current = await _run(lambda: ads.get_ad(ad_id))
    req = WriteRequest(
        action="ad.resume",
        entity="ad",
        entity_id=ad_id,
        summary=f"Resume '{current.name}'",
        params={"ad_id": ad_id},
        actor=user.email,
        source="rest_api",
        is_spend_increasing=True,
        before=current.model_dump(),
    )
    return await _do_write(db, req)


class CreateAdRequest(BaseModel):
    name: str
    adset_id: str
    creative_id: str


@router.post("/ads", response_model=WriteResponse)
async def create_ad(
    body: CreateAdRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WriteResponse:
    adset = await _run(lambda: adsets.get_adset(body.adset_id))
    req = WriteRequest(
        action="ad.create",
        entity="ad",
        entity_id=None,
        summary=f"Create ad '{body.name}' in ad set {body.adset_id} (starts PAUSED)",
        params=body.model_dump(),
        actor=user.email,
        source="rest_api",
        new_ad_campaign_id=adset.campaign_id,
    )
    return await _do_write(db, req)


# ---- assets ----------------------------------------------------------------


@router.post("/assets/image", response_model=WriteResponse)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WriteResponse:
    file_bytes = await file.read()
    outcome = await run_asset_upload(
        db,
        action="asset.upload_image",
        actor=user.email,
        source="rest_api",
        metadata={"filename": file.filename, "size_bytes": len(file_bytes)},
        upload_fn=lambda: assets.upload_image(file_bytes),
    )
    return WriteResponse(
        status=outcome.status, result=outcome.result, approval_id=outcome.approval_id, reason=outcome.reason
    )


@router.post("/assets/video", response_model=WriteResponse)
async def upload_video(
    name: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WriteResponse:
    file_bytes = await file.read()
    outcome = await run_asset_upload(
        db,
        action="asset.upload_video",
        actor=user.email,
        source="rest_api",
        metadata={"filename": file.filename, "name": name, "size_bytes": len(file_bytes)},
        upload_fn=lambda: assets.upload_video(file_bytes, name=name),
    )
    return WriteResponse(
        status=outcome.status, result=outcome.result, approval_id=outcome.approval_id, reason=outcome.reason
    )


# ---- creatives ---------------------------------------------------------------


@router.get("/creatives", response_model=list[Creative])
async def get_creatives() -> list[Creative]:
    creative_list = await _run(creatives.list_creatives)
    all_ads = await _run(ads.list_ads)
    usage = Counter(a.creative_id for a in all_ads if a.creative_id)
    for c in creative_list:
        c.usage_count = usage.get(c.id, 0)
    return creative_list


class CreateCreativeRequest(BaseModel):
    name: str
    message: str
    link: str
    headline: str
    call_to_action: str = "LEARN_MORE"
    image_hash: str | None = None
    video_id: str | None = None


@router.post("/creatives", response_model=WriteResponse)
async def create_creative(
    body: CreateCreativeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WriteResponse:
    req = WriteRequest(
        action="creative.create",
        entity="creative",
        entity_id=None,
        summary=f"Create creative '{body.name}'",
        params=body.model_dump(),
        actor=user.email,
        source="rest_api",
    )
    return await _do_write(db, req)
