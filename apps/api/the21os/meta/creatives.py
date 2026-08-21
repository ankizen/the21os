from facebook_business.adobjects.adcreative import AdCreative as FbAdCreative

from the21os.meta.client import call_meta, ensure_initialized, get_account
from the21os.meta.models import Creative

_FIELDS = [
    FbAdCreative.Field.id,
    FbAdCreative.Field.name,
    FbAdCreative.Field.status,
    FbAdCreative.Field.thumbnail_url,
    FbAdCreative.Field.image_url,
    FbAdCreative.Field.video_id,
    FbAdCreative.Field.object_type,
    FbAdCreative.Field.body,
    FbAdCreative.Field.title,
    FbAdCreative.Field.call_to_action_type,
]


async def list_creatives(account_id: str | None = None) -> list[Creative]:
    account = get_account(account_id)

    def fetch() -> list[dict]:
        return [dict(c) for c in account.get_ad_creatives(fields=_FIELDS, params={"limit": 100})]

    rows = await call_meta(fetch)
    return [Creative.model_validate(r) for r in rows]


async def get_creative(creative_id: str) -> Creative:
    def fetch() -> dict:
        ensure_initialized()
        creative = FbAdCreative(creative_id)
        creative.api_get(fields=_FIELDS)
        return dict(creative)

    data = await call_meta(fetch)
    return Creative.model_validate(data)


async def get_default_page_id(account_id: str | None = None) -> str:
    """The single business Page this account promotes as — auto-detected
    rather than configured, since this is a one-page business. If that
    stops being true, this is the one place to change."""
    account = get_account(account_id)

    def fetch() -> list[dict]:
        return [dict(p) for p in account.get_promote_pages(fields=["id", "name"])]

    pages = await call_meta(fetch)
    if not pages:
        raise ValueError("No Facebook Page is available to this ad account to post creatives as.")
    return pages[0]["id"]


async def create_creative(
    name: str,
    message: str,
    link: str,
    headline: str,
    call_to_action: str = "LEARN_MORE",
    image_hash: str | None = None,
    video_id: str | None = None,
    account_id: str | None = None,
) -> Creative:
    if not image_hash and not video_id:
        raise ValueError("A creative needs either image_hash or video_id.")
    account = get_account(account_id)
    page_id = await get_default_page_id(account_id)

    def fetch() -> dict:
        link_data: dict = {"link": link, "message": message, "name": headline}
        story_spec: dict = {"page_id": page_id}
        if video_id:
            story_spec["video_data"] = {
                "video_id": video_id,
                "message": message,
                "title": headline,
                "call_to_action": {"type": call_to_action, "value": {"link": link}},
            }
        else:
            link_data["image_hash"] = image_hash
            link_data["call_to_action"] = {"type": call_to_action}
            story_spec["link_data"] = link_data

        params = {FbAdCreative.Field.name: name, "object_story_spec": story_spec}
        created = account.create_ad_creative(fields=_FIELDS, params=params)
        return dict(created)

    data = await call_meta(fetch)
    return Creative.model_validate(data)
