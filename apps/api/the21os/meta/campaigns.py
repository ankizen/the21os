from facebook_business.adobjects.campaign import Campaign as FbCampaign

from the21os.meta.client import call_meta, ensure_initialized, get_account
from the21os.meta.models import Campaign

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


async def create_campaign(
    name: str, objective: str, daily_budget_cents: int, account_id: str | None = None
) -> Campaign:
    """Always created PAUSED — no caller, including Claude, can create a
    live campaign directly. Promoting to ACTIVE is a separate, explicit
    resume action, itself gated by the same safety pipeline."""
    account = get_account(account_id)

    def fetch() -> dict:
        params = {
            FbCampaign.Field.name: name,
            FbCampaign.Field.objective: objective,
            FbCampaign.Field.status: FbCampaign.Status.paused,
            "special_ad_categories": [],
            FbCampaign.Field.daily_budget: str(daily_budget_cents),
        }
        created = account.create_campaign(fields=_FIELDS, params=params)
        return dict(created)

    data = await call_meta(fetch)
    return Campaign.model_validate(data)


async def update_campaign_budget(campaign_id: str, daily_budget_cents: int) -> Campaign:
    def fetch() -> dict:
        ensure_initialized()
        campaign = FbCampaign(campaign_id)
        campaign.api_update(params={FbCampaign.Field.daily_budget: str(daily_budget_cents)})
        campaign.api_get(fields=_FIELDS)
        return dict(campaign)

    data = await call_meta(fetch)
    return Campaign.model_validate(data)


async def set_campaign_status(campaign_id: str, status: str) -> Campaign:
    def fetch() -> dict:
        ensure_initialized()
        campaign = FbCampaign(campaign_id)
        campaign.api_update(params={FbCampaign.Field.status: status})
        campaign.api_get(fields=_FIELDS)
        return dict(campaign)

    data = await call_meta(fetch)
    return Campaign.model_validate(data)


async def duplicate_campaign(campaign_id: str, name_suffix: str = " (copy)") -> Campaign:
    """Campaign-level duplication only — copies name/objective/budget as a
    new PAUSED campaign. Does not duplicate ad sets, ads, or creatives; that
    needs targeting (ad sets) and creative assets (Phase 4) this system
    doesn't manage yet. Rather than a shallow, silently-incomplete "full"
    duplicate, this is honest about being campaign-shell-only."""
    source = await get_campaign(campaign_id)
    return await create_campaign(
        name=f"{source.name}{name_suffix}",
        objective=source.objective or "OUTCOME_SALES",
        daily_budget_cents=int(source.daily_budget) if source.daily_budget else 0,
    )
