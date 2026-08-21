from collections.abc import Awaitable, Callable
from typing import TypeVar

from facebook_business.exceptions import FacebookRequestError
from fastapi import APIRouter, Depends, HTTPException, Query

from the21secrets.auth.dependencies import get_current_user
from the21secrets.meta import accounts, ads, adsets, campaigns, insights
from the21secrets.meta.client import MetaNotConfigured
from the21secrets.meta.models import AccountInfo, Ad, AdSet, Campaign
from the21secrets.meta.models import Insights as InsightsModel

router = APIRouter(prefix="/api/meta", tags=["meta"], dependencies=[Depends(get_current_user)])

T = TypeVar("T")


async def _run(fn: Callable[[], Awaitable[T]]) -> T:
    try:
        return await fn()
    except MetaNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except FacebookRequestError as e:
        raise HTTPException(
            status_code=502,
            detail=e.api_error_message() or "Meta API request failed",
        ) from e


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
