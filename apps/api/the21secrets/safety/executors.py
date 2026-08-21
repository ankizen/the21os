"""Registry of write actions by name, mapping to the raw meta/ functions.

Needed because an action that requires approval can't just be a closure —
it has to survive being stored in the database (ApprovalRequest.params_json)
and executed later, possibly by a different request entirely. Every write
action is registered here under the same name used in audit_log.action, so
"what ran" and "what could be replayed" are always the same string."""

from collections.abc import Awaitable, Callable

from the21secrets.meta import ads, adsets, campaigns

Executor = Callable[[dict], Awaitable[dict]]

_EXECUTORS: dict[str, Executor] = {}


def register(name: str) -> Callable[[Executor], Executor]:
    def decorator(fn: Executor) -> Executor:
        _EXECUTORS[name] = fn
        return fn

    return decorator


async def execute(action: str, params: dict) -> dict:
    if action not in _EXECUTORS:
        raise KeyError(f"No executor registered for action {action!r}")
    return await _EXECUTORS[action](params)


@register("campaign.create")
async def _campaign_create(params: dict) -> dict:
    c = await campaigns.create_campaign(
        name=params["name"], objective=params["objective"], daily_budget_cents=params["daily_budget_cents"]
    )
    return c.model_dump()


@register("campaign.budget_update")
async def _campaign_budget_update(params: dict) -> dict:
    c = await campaigns.update_campaign_budget(
        campaign_id=params["campaign_id"], daily_budget_cents=params["daily_budget_cents"]
    )
    return c.model_dump()


@register("campaign.pause")
async def _campaign_pause(params: dict) -> dict:
    c = await campaigns.set_campaign_status(params["campaign_id"], "PAUSED")
    return c.model_dump()


@register("campaign.resume")
async def _campaign_resume(params: dict) -> dict:
    c = await campaigns.set_campaign_status(params["campaign_id"], "ACTIVE")
    return c.model_dump()


@register("campaign.duplicate")
async def _campaign_duplicate(params: dict) -> dict:
    c = await campaigns.duplicate_campaign(
        params["campaign_id"], name_suffix=params.get("name_suffix", " (copy)")
    )
    return c.model_dump()


@register("adset.budget_update")
async def _adset_budget_update(params: dict) -> dict:
    a = await adsets.update_adset_budget(
        adset_id=params["adset_id"], daily_budget_cents=params["daily_budget_cents"]
    )
    return a.model_dump()


@register("adset.pause")
async def _adset_pause(params: dict) -> dict:
    a = await adsets.set_adset_status(params["adset_id"], "PAUSED")
    return a.model_dump()


@register("adset.resume")
async def _adset_resume(params: dict) -> dict:
    a = await adsets.set_adset_status(params["adset_id"], "ACTIVE")
    return a.model_dump()


@register("ad.pause")
async def _ad_pause(params: dict) -> dict:
    a = await ads.set_ad_status(params["ad_id"], "PAUSED")
    return a.model_dump()


@register("ad.resume")
async def _ad_resume(params: dict) -> dict:
    a = await ads.set_ad_status(params["ad_id"], "ACTIVE")
    return a.model_dump()
