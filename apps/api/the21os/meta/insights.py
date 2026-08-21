from facebook_business.adobjects.adsinsights import AdsInsights as FbAdsInsights

from the21os.core.metrics import calc_cpa, calc_roas, extract_purchase_value, extract_purchases
from the21os.meta.client import call_meta, get_account
from the21os.meta.models import Insights

_FIELDS = [
    FbAdsInsights.Field.impressions,
    FbAdsInsights.Field.clicks,
    FbAdsInsights.Field.spend,
    FbAdsInsights.Field.reach,
    FbAdsInsights.Field.ctr,
    FbAdsInsights.Field.cpc,
    FbAdsInsights.Field.cpm,
    FbAdsInsights.Field.actions,
    FbAdsInsights.Field.action_values,
    FbAdsInsights.Field.date_start,
    FbAdsInsights.Field.date_stop,
]

_CAMPAIGN_FIELDS = [*_FIELDS, FbAdsInsights.Field.campaign_id, FbAdsInsights.Field.campaign_name]


def _to_insights(row: dict, entity_id: str | None = None, entity_name: str | None = None) -> Insights:
    spend = float(row.get("spend") or 0)
    purchases = extract_purchases(row.get("actions"))
    purchase_value = extract_purchase_value(row.get("action_values"))
    return Insights(
        entity_id=entity_id,
        entity_name=entity_name,
        impressions=int(row.get("impressions") or 0),
        clicks=int(row.get("clicks") or 0),
        spend=spend,
        reach=int(row["reach"]) if row.get("reach") else None,
        ctr=float(row["ctr"]) if row.get("ctr") else None,
        cpc=float(row["cpc"]) if row.get("cpc") else None,
        cpm=float(row["cpm"]) if row.get("cpm") else None,
        purchases=purchases,
        purchase_value=purchase_value,
        cpa=calc_cpa(spend, purchases),
        roas=calc_roas(purchase_value, spend),
        date_start=row.get("date_start"),
        date_stop=row.get("date_stop"),
    )


async def get_account_insights(date_preset: str = "today", account_id: str | None = None) -> Insights:
    account = get_account(account_id)

    def fetch() -> dict | None:
        rows = list(account.get_insights(fields=_FIELDS, params={"date_preset": date_preset}))
        return dict(rows[0]) if rows else None

    row = await call_meta(fetch)
    return _to_insights(row or {})


async def get_campaign_insights(date_preset: str = "today", account_id: str | None = None) -> list[Insights]:
    """Per-campaign breakdown for the given date preset — one Meta API call
    covering every campaign, not one call per campaign."""
    account = get_account(account_id)

    def fetch() -> list[dict]:
        return [
            dict(r)
            for r in account.get_insights(
                fields=_CAMPAIGN_FIELDS, params={"level": "campaign", "date_preset": date_preset}
            )
        ]

    rows = await call_meta(fetch)
    return [_to_insights(r, entity_id=r.get("campaign_id"), entity_name=r.get("campaign_name")) for r in rows]
