from facebook_business.adobjects.adset import AdSet as FbAdSet
from facebook_business.adobjects.campaign import Campaign as FbCampaign

from the21secrets.meta.client import call_meta, ensure_initialized, get_account
from the21secrets.meta.models import AdSet

_FIELDS = [
    FbAdSet.Field.id,
    FbAdSet.Field.name,
    FbAdSet.Field.status,
    FbAdSet.Field.effective_status,
    FbAdSet.Field.campaign_id,
    FbAdSet.Field.optimization_goal,
    FbAdSet.Field.daily_budget,
    FbAdSet.Field.lifetime_budget,
]


async def list_adsets(campaign_id: str | None = None, account_id: str | None = None) -> list[AdSet]:
    def fetch() -> list[dict]:
        if campaign_id:
            ensure_initialized()
            cursor = FbCampaign(campaign_id).get_ad_sets(fields=_FIELDS, params={"limit": 100})
        else:
            cursor = get_account(account_id).get_ad_sets(fields=_FIELDS, params={"limit": 100})
        return [dict(a) for a in cursor]

    rows = await call_meta(fetch)
    return [AdSet.model_validate(r) for r in rows]


async def get_adset(adset_id: str) -> AdSet:
    def fetch() -> dict:
        ensure_initialized()
        adset = FbAdSet(adset_id)
        adset.api_get(fields=_FIELDS)
        return dict(adset)

    data = await call_meta(fetch)
    return AdSet.model_validate(data)


async def update_adset_budget(adset_id: str, daily_budget_cents: int) -> AdSet:
    def fetch() -> dict:
        ensure_initialized()
        adset = FbAdSet(adset_id)
        adset.api_update(params={FbAdSet.Field.daily_budget: str(daily_budget_cents)})
        adset.api_get(fields=_FIELDS)
        return dict(adset)

    data = await call_meta(fetch)
    return AdSet.model_validate(data)


async def set_adset_status(adset_id: str, status: str) -> AdSet:
    def fetch() -> dict:
        ensure_initialized()
        adset = FbAdSet(adset_id)
        adset.api_update(params={FbAdSet.Field.status: status})
        adset.api_get(fields=_FIELDS)
        return dict(adset)

    data = await call_meta(fetch)
    return AdSet.model_validate(data)
