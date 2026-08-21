from facebook_business.adobjects.campaign import Campaign as FbCampaign

from the21secrets.meta.client import call_meta, ensure_initialized, get_account
from the21secrets.meta.models import Campaign

_FIELDS = [
    FbCampaign.Field.id,
    FbCampaign.Field.name,
    FbCampaign.Field.status,
    FbCampaign.Field.effective_status,
    FbCampaign.Field.objective,
    FbCampaign.Field.daily_budget,
    FbCampaign.Field.lifetime_budget,
]


async def list_campaigns(account_id: str | None = None) -> list[Campaign]:
    account = get_account(account_id)

    def fetch() -> list[dict]:
        return [dict(c) for c in account.get_campaigns(fields=_FIELDS, params={"limit": 100})]

    rows = await call_meta(fetch)
    return [Campaign.model_validate(r) for r in rows]


async def get_campaign(campaign_id: str) -> Campaign:
    def fetch() -> dict:
        ensure_initialized()
        campaign = FbCampaign(campaign_id)
        campaign.api_get(fields=_FIELDS)
        return dict(campaign)

    data = await call_meta(fetch)
    return Campaign.model_validate(data)
