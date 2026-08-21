from facebook_business.adobjects.ad import Ad as FbAd
from facebook_business.adobjects.adset import AdSet as FbAdSet
from facebook_business.adobjects.campaign import Campaign as FbCampaign

from the21os.meta.client import call_meta, ensure_initialized, get_account
from the21os.meta.models import Ad

_FIELDS = [
    FbAd.Field.id,
    FbAd.Field.name,
    FbAd.Field.status,
    FbAd.Field.effective_status,
    FbAd.Field.adset_id,
    FbAd.Field.campaign_id,
    FbAd.Field.creative,
]


def _flatten(row: dict) -> dict:
    """The `creative` field comes back as a nested {"id": ...} object —
    flatten it to creative_id to match our Ad model."""
    creative = row.pop("creative", None)
    row["creative_id"] = creative.get("id") if creative else None
    return row


async def list_ads(adset_id: str | None = None, account_id: str | None = None) -> list[Ad]:
    def fetch() -> list[dict]:
        if adset_id:
            ensure_initialized()
            cursor = FbAdSet(adset_id).get_ads(fields=_FIELDS, params={"limit": 100})
        else:
            cursor = get_account(account_id).get_ads(fields=_FIELDS, params={"limit": 100})
        return [_flatten(dict(a)) for a in cursor]

    rows = await call_meta(fetch)
    return [Ad.model_validate(r) for r in rows]


async def get_ad(ad_id: str) -> Ad:
    def fetch() -> dict:
        ensure_initialized()
        ad = FbAd(ad_id)
        ad.api_get(fields=_FIELDS)
        return _flatten(dict(ad))

    data = await call_meta(fetch)
    return Ad.model_validate(data)


async def set_ad_status(ad_id: str, status: str) -> Ad:
    def fetch() -> dict:
        ensure_initialized()
        ad = FbAd(ad_id)
        ad.api_update(params={FbAd.Field.status: status})
        ad.api_get(fields=_FIELDS)
        return _flatten(dict(ad))

    data = await call_meta(fetch)
    return Ad.model_validate(data)


async def count_ads_in_campaign(campaign_id: str) -> int:
    def fetch() -> int:
        ensure_initialized()
        cursor = FbCampaign(campaign_id).get_ads(fields=[FbAd.Field.id], params={"limit": 500})
        return len(list(cursor))

    return await call_meta(fetch)


async def create_ad(name: str, adset_id: str, creative_id: str, account_id: str | None = None) -> Ad:
    """Always created PAUSED, same as campaigns — see create_campaign."""
    account = get_account(account_id)

    def fetch() -> dict:
        params = {
            FbAd.Field.name: name,
            FbAd.Field.adset_id: adset_id,
            "creative": {"creative_id": creative_id},
            FbAd.Field.status: FbAd.Status.paused,
        }
        created = account.create_ad(fields=_FIELDS, params=params)
        return _flatten(dict(created))

    data = await call_meta(fetch)
    return Ad.model_validate(data)
