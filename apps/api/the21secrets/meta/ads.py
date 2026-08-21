from facebook_business.adobjects.ad import Ad as FbAd
from facebook_business.adobjects.adset import AdSet as FbAdSet

from the21secrets.meta.client import call_meta, ensure_initialized, get_account
from the21secrets.meta.models import Ad

_FIELDS = [
    FbAd.Field.id,
    FbAd.Field.name,
    FbAd.Field.status,
    FbAd.Field.effective_status,
    FbAd.Field.adset_id,
    FbAd.Field.campaign_id,
]


async def list_ads(adset_id: str | None = None, account_id: str | None = None) -> list[Ad]:
    def fetch() -> list[dict]:
        if adset_id:
            ensure_initialized()
            cursor = FbAdSet(adset_id).get_ads(fields=_FIELDS, params={"limit": 100})
        else:
            cursor = get_account(account_id).get_ads(fields=_FIELDS, params={"limit": 100})
        return [dict(a) for a in cursor]

    rows = await call_meta(fetch)
    return [Ad.model_validate(r) for r in rows]


async def get_ad(ad_id: str) -> Ad:
    def fetch() -> dict:
        ensure_initialized()
        ad = FbAd(ad_id)
        ad.api_get(fields=_FIELDS)
        return dict(ad)

    data = await call_meta(fetch)
    return Ad.model_validate(data)


async def set_ad_status(ad_id: str, status: str) -> Ad:
    def fetch() -> dict:
        ensure_initialized()
        ad = FbAd(ad_id)
        ad.api_update(params={FbAd.Field.status: status})
        ad.api_get(fields=_FIELDS)
        return dict(ad)

    data = await call_meta(fetch)
    return Ad.model_validate(data)
