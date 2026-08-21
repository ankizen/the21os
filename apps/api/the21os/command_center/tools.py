"""Tool schemas + in-process dispatch for the Command Center's Claude
tool-use loop. Every function here is a thin wrapper around an existing
meta/ or ga4/ function — no new business logic, so "Claude reasons, code
calculates" (master prompt SS15) holds simply because these are the exact
functions the REST API already calls.

Writes go through the same safety.pipeline.run_write() as the REST API,
with source="command_center" — the safety gate does not know or care that
Claude asked instead of a human clicking a button."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx
from facebook_business.exceptions import FacebookRequestError
from google.api_core.exceptions import GoogleAPICallError
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.core.correlation import correlate_campaigns
from the21os.db.models import User, WordPressConnection
from the21os.ga4 import accounts as ga4_accounts
from the21os.ga4 import realtime as ga4_realtime
from the21os.ga4 import reports as ga4_reports
from the21os.ga4.client import GA4NotConfigured
from the21os.meta import accounts as meta_accounts
from the21os.meta import ads, adsets, campaigns, creatives
from the21os.meta import insights as meta_insights
from the21os.meta.client import MetaNotConfigured
from the21os.safety.pipeline import WriteRequest, run_write
from the21os.wordpress.client import WordPressNotConfigured
from the21os.wordpress.orders import orders_summary


@dataclass
class ToolContext:
    db: AsyncSession
    user: User


ToolFn = Callable[[dict, ToolContext], Awaitable[dict]]

_DISPATCH: dict[str, ToolFn] = {}


def _tool(name: str) -> Callable[[ToolFn], ToolFn]:
    def decorator(fn: ToolFn) -> ToolFn:
        _DISPATCH[name] = fn
        return fn

    return decorator


async def run_tool(name: str, params: dict, ctx: ToolContext) -> dict:
    if name not in _DISPATCH:
        return {"error": f"Unknown tool {name!r}"}
    try:
        return await _DISPATCH[name](params, ctx)
    except (MetaNotConfigured, GA4NotConfigured, WordPressNotConfigured, ValueError) as e:
        return {"error": str(e)}
    except FacebookRequestError as e:
        return {"error": e.api_error_message() or "Meta API request failed"}
    except GoogleAPICallError as e:
        return {"error": str(e.message) or "GA4 API request failed"}
    except httpx.HTTPError as e:
        return {"error": f"WordPress/WooCommerce API request failed: {e}"}


def _actor(ctx: ToolContext) -> str:
    return f"claude:{ctx.user.email}"


async def _write(ctx: ToolContext, req: WriteRequest) -> dict:
    outcome = await run_write(ctx.db, req)
    return {
        "status": outcome.status,
        "result": outcome.result,
        "approval_id": outcome.approval_id,
        "reason": outcome.reason,
    }


# ---- Meta reads -------------------------------------------------------


@_tool("meta_get_account_info")
async def _t_meta_account(params: dict, ctx: ToolContext) -> dict:
    info = await meta_accounts.get_account_info()
    return info.model_dump()


@_tool("meta_list_campaigns")
async def _t_list_campaigns(params: dict, ctx: ToolContext) -> dict:
    rows = await campaigns.list_campaigns()
    return {"campaigns": [c.model_dump() for c in rows]}


@_tool("meta_get_campaign")
async def _t_get_campaign(params: dict, ctx: ToolContext) -> dict:
    c = await campaigns.get_campaign(params["campaign_id"])
    return c.model_dump()


@_tool("meta_list_adsets")
async def _t_list_adsets(params: dict, ctx: ToolContext) -> dict:
    rows = await adsets.list_adsets(campaign_id=params.get("campaign_id"))
    return {"adsets": [a.model_dump() for a in rows]}


@_tool("meta_get_adset")
async def _t_get_adset(params: dict, ctx: ToolContext) -> dict:
    a = await adsets.get_adset(params["adset_id"])
    return a.model_dump()


@_tool("meta_list_ads")
async def _t_list_ads(params: dict, ctx: ToolContext) -> dict:
    rows = await ads.list_ads(adset_id=params.get("adset_id"))
    return {"ads": [a.model_dump() for a in rows]}


@_tool("meta_get_ad")
async def _t_get_ad(params: dict, ctx: ToolContext) -> dict:
    a = await ads.get_ad(params["ad_id"])
    return a.model_dump()


@_tool("meta_list_creatives")
async def _t_list_creatives(params: dict, ctx: ToolContext) -> dict:
    rows = await creatives.list_creatives()
    return {"creatives": [c.model_dump() for c in rows]}


@_tool("meta_get_creative")
async def _t_get_creative(params: dict, ctx: ToolContext) -> dict:
    c = await creatives.get_creative(params["creative_id"])
    return c.model_dump()


@_tool("meta_get_account_insights")
async def _t_account_insights(params: dict, ctx: ToolContext) -> dict:
    i = await meta_insights.get_account_insights(date_preset=params.get("date_preset", "today"))
    return i.model_dump()


@_tool("meta_get_campaign_insights")
async def _t_campaign_insights(params: dict, ctx: ToolContext) -> dict:
    rows = await meta_insights.get_campaign_insights(date_preset=params.get("date_preset", "today"))
    return {"insights": [i.model_dump() for i in rows]}


# ---- GA4 reads ----------------------------------------------------------


@_tool("ga4_run_report")
async def _t_ga4_run_report(params: dict, ctx: ToolContext) -> dict:
    report = await ga4_reports.run_report(
        dimensions=params["dimensions"],
        metrics=params["metrics"],
        start_date=params.get("start_date", "28daysAgo"),
        end_date=params.get("end_date", "today"),
    )
    return report.model_dump()


@_tool("ga4_landing_page_report")
async def _t_ga4_landing(params: dict, ctx: ToolContext) -> dict:
    r = await ga4_reports.landing_page_report(
        params.get("start_date", "28daysAgo"), params.get("end_date", "today")
    )
    return r.model_dump()


@_tool("ga4_campaign_report")
async def _t_ga4_campaign(params: dict, ctx: ToolContext) -> dict:
    r = await ga4_reports.campaign_report(
        params.get("start_date", "28daysAgo"), params.get("end_date", "today")
    )
    return r.model_dump()


@_tool("ga4_traffic_source_report")
async def _t_ga4_traffic(params: dict, ctx: ToolContext) -> dict:
    r = await ga4_reports.traffic_source_report(
        params.get("start_date", "28daysAgo"), params.get("end_date", "today")
    )
    return r.model_dump()


@_tool("ga4_conversion_report")
async def _t_ga4_conversion(params: dict, ctx: ToolContext) -> dict:
    r = await ga4_reports.conversion_report(
        params.get("start_date", "28daysAgo"), params.get("end_date", "today")
    )
    return r.model_dump()


@_tool("ga4_revenue_report")
async def _t_ga4_revenue(params: dict, ctx: ToolContext) -> dict:
    r = await ga4_reports.revenue_report(
        params.get("start_date", "28daysAgo"), params.get("end_date", "today")
    )
    return r.model_dump()


@_tool("ga4_realtime_report")
async def _t_ga4_realtime(params: dict, ctx: ToolContext) -> dict:
    r = await ga4_realtime.realtime_report()
    return r.model_dump()


@_tool("ga4_property_info")
async def _t_ga4_property(params: dict, ctx: ToolContext) -> dict:
    p = await ga4_accounts.get_property_info()
    return p.model_dump()


# ---- correlation --------------------------------------------------------


@_tool("analytics_correlate_campaigns")
async def _t_correlate(params: dict, ctx: ToolContext) -> dict:
    date_preset = params.get("date_preset", "last_30d")
    start_date = params.get("start_date", "28daysAgo")
    end_date = params.get("end_date", "today")
    meta_data = await meta_insights.get_campaign_insights(date_preset=date_preset)
    ga4_data = await ga4_reports.campaign_report(start_date=start_date, end_date=end_date)
    meta_rows = [
        {
            "campaign_id": m.entity_id,
            "campaign_name": m.entity_name or m.entity_id,
            "spend": m.spend,
            "purchases": m.purchases,
            "purchase_value": m.purchase_value,
        }
        for m in meta_data
        if m.entity_id
    ]
    ga4_rows = [
        {
            "campaign_id": row.dimensions.get("sessionCampaignName", ""),
            "sessions": row.metrics.get("sessions", 0.0),
            "users": row.metrics.get("totalUsers", 0.0),
            "key_events": row.metrics.get("keyEvents", 0.0),
            "revenue": row.metrics.get("totalRevenue", 0.0),
        }
        for row in ga4_data.rows
    ]
    return {"rows": correlate_campaigns(meta_rows, ga4_rows)}


@_tool("woo_orders_summary")
async def _t_woo_orders_summary(params: dict, ctx: ToolContext) -> dict:
    conn = await ctx.db.get(WordPressConnection, 1)
    if conn is None:
        raise WordPressNotConfigured("WordPress/WooCommerce is not connected")
    return await orders_summary(conn, params.get("date_preset", "today"))


# ---- Meta writes ----------------------------------------------------------


@_tool("meta_create_campaign")
async def _t_create_campaign(params: dict, ctx: ToolContext) -> dict:
    daily_budget_cents = params["daily_budget_cents"]
    req = WriteRequest(
        action="campaign.create",
        entity="campaign",
        entity_id=None,
        summary=f"Create campaign '{params['name']}' (₹{daily_budget_cents / 100:.2f}/day, starts PAUSED)",
        params={
            "name": params["name"],
            "objective": params["objective"],
            "daily_budget_cents": daily_budget_cents,
        },
        actor=_actor(ctx),
        source="command_center",
        budget_cents=daily_budget_cents,
        is_new_campaign=True,
    )
    return await _write(ctx, req)


@_tool("meta_update_campaign_budget")
async def _t_update_campaign_budget(params: dict, ctx: ToolContext) -> dict:
    campaign_id = params["campaign_id"]
    new_cents = params["daily_budget_cents"]
    current = await campaigns.get_campaign(campaign_id)
    previous_cents = int(current.daily_budget) if current.daily_budget else 0
    req = WriteRequest(
        action="campaign.budget_update",
        entity="campaign",
        entity_id=campaign_id,
        summary=f"Update '{current.name}' daily budget to ₹{new_cents / 100:.2f}",
        params={"campaign_id": campaign_id, "daily_budget_cents": new_cents},
        actor=_actor(ctx),
        source="command_center",
        budget_cents=new_cents,
        previous_budget_cents=previous_cents,
        is_spend_increasing=new_cents > previous_cents,
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_pause_campaign")
async def _t_pause_campaign(params: dict, ctx: ToolContext) -> dict:
    campaign_id = params["campaign_id"]
    current = await campaigns.get_campaign(campaign_id)
    req = WriteRequest(
        action="campaign.pause",
        entity="campaign",
        entity_id=campaign_id,
        summary=f"Pause '{current.name}'",
        params={"campaign_id": campaign_id},
        actor=_actor(ctx),
        source="command_center",
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_resume_campaign")
async def _t_resume_campaign(params: dict, ctx: ToolContext) -> dict:
    campaign_id = params["campaign_id"]
    current = await campaigns.get_campaign(campaign_id)
    req = WriteRequest(
        action="campaign.resume",
        entity="campaign",
        entity_id=campaign_id,
        summary=f"Resume '{current.name}'",
        params={"campaign_id": campaign_id},
        actor=_actor(ctx),
        source="command_center",
        is_spend_increasing=True,
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_duplicate_campaign")
async def _t_duplicate_campaign(params: dict, ctx: ToolContext) -> dict:
    campaign_id = params["campaign_id"]
    name_suffix = params.get("name_suffix", " (copy)")
    source = await campaigns.get_campaign(campaign_id)
    budget_cents = int(source.daily_budget) if source.daily_budget else 0
    req = WriteRequest(
        action="campaign.duplicate",
        entity="campaign",
        entity_id=None,
        summary=f"Duplicate '{source.name}' (campaign shell only — no ad sets/ads/creatives)",
        params={"campaign_id": campaign_id, "name_suffix": name_suffix},
        actor=_actor(ctx),
        source="command_center",
        budget_cents=budget_cents,
        is_new_campaign=True,
    )
    return await _write(ctx, req)


@_tool("meta_update_adset_budget")
async def _t_update_adset_budget(params: dict, ctx: ToolContext) -> dict:
    adset_id = params["adset_id"]
    new_cents = params["daily_budget_cents"]
    current = await adsets.get_adset(adset_id)
    previous_cents = int(current.daily_budget) if current.daily_budget else 0
    req = WriteRequest(
        action="adset.budget_update",
        entity="adset",
        entity_id=adset_id,
        summary=f"Update '{current.name}' daily budget to ₹{new_cents / 100:.2f}",
        params={"adset_id": adset_id, "daily_budget_cents": new_cents},
        actor=_actor(ctx),
        source="command_center",
        budget_cents=new_cents,
        previous_budget_cents=previous_cents,
        is_spend_increasing=new_cents > previous_cents,
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_pause_adset")
async def _t_pause_adset(params: dict, ctx: ToolContext) -> dict:
    adset_id = params["adset_id"]
    current = await adsets.get_adset(adset_id)
    req = WriteRequest(
        action="adset.pause",
        entity="adset",
        entity_id=adset_id,
        summary=f"Pause '{current.name}'",
        params={"adset_id": adset_id},
        actor=_actor(ctx),
        source="command_center",
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_resume_adset")
async def _t_resume_adset(params: dict, ctx: ToolContext) -> dict:
    adset_id = params["adset_id"]
    current = await adsets.get_adset(adset_id)
    req = WriteRequest(
        action="adset.resume",
        entity="adset",
        entity_id=adset_id,
        summary=f"Resume '{current.name}'",
        params={"adset_id": adset_id},
        actor=_actor(ctx),
        source="command_center",
        is_spend_increasing=True,
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_pause_ad")
async def _t_pause_ad(params: dict, ctx: ToolContext) -> dict:
    ad_id = params["ad_id"]
    current = await ads.get_ad(ad_id)
    req = WriteRequest(
        action="ad.pause",
        entity="ad",
        entity_id=ad_id,
        summary=f"Pause '{current.name}'",
        params={"ad_id": ad_id},
        actor=_actor(ctx),
        source="command_center",
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_resume_ad")
async def _t_resume_ad(params: dict, ctx: ToolContext) -> dict:
    ad_id = params["ad_id"]
    current = await ads.get_ad(ad_id)
    req = WriteRequest(
        action="ad.resume",
        entity="ad",
        entity_id=ad_id,
        summary=f"Resume '{current.name}'",
        params={"ad_id": ad_id},
        actor=_actor(ctx),
        source="command_center",
        is_spend_increasing=True,
        before=current.model_dump(),
    )
    return await _write(ctx, req)


@_tool("meta_create_ad")
async def _t_create_ad(params: dict, ctx: ToolContext) -> dict:
    adset_id = params["adset_id"]
    adset = await adsets.get_adset(adset_id)
    req = WriteRequest(
        action="ad.create",
        entity="ad",
        entity_id=None,
        summary=f"Create ad '{params['name']}' in ad set {adset_id} (starts PAUSED)",
        params={"name": params["name"], "adset_id": adset_id, "creative_id": params["creative_id"]},
        actor=_actor(ctx),
        source="command_center",
        new_ad_campaign_id=adset.campaign_id,
    )
    return await _write(ctx, req)


@_tool("meta_create_creative")
async def _t_create_creative(params: dict, ctx: ToolContext) -> dict:
    body = {
        "name": params["name"],
        "message": params["message"],
        "link": params["link"],
        "headline": params["headline"],
        "call_to_action": params.get("call_to_action", "LEARN_MORE"),
        "image_hash": params.get("image_hash"),
        "video_id": params.get("video_id"),
    }
    req = WriteRequest(
        action="creative.create",
        entity="creative",
        entity_id=None,
        summary=f"Create creative '{params['name']}'",
        params=body,
        actor=_actor(ctx),
        source="command_center",
    )
    return await _write(ctx, req)


# ---- tool schemas (Anthropic Messages API `tools` format) ---------------

_ID = {"type": "string", "description": "Meta object id"}
_DATE_RANGE_PROPS: dict[str, Any] = {
    "start_date": {"type": "string", "description": "GA4 date, e.g. '28daysAgo' or 'YYYY-MM-DD'"},
    "end_date": {"type": "string", "description": "GA4 date, e.g. 'today' or 'YYYY-MM-DD'"},
}
_DATE_PRESET_PROP: dict[str, Any] = {
    "date_preset": {
        "type": "string",
        "description": "Meta insights date_preset, e.g. 'today', 'yesterday', 'last_7d', 'last_30d'",
    }
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "meta_get_account_info",
        "description": "Get the ad account's name, currency, timezone, status, and lifetime amount spent.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "meta_list_campaigns",
        "description": "List all campaigns in the ad account.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "meta_get_campaign",
        "description": "Get one campaign by id.",
        "input_schema": {
            "type": "object",
            "properties": {"campaign_id": _ID},
            "required": ["campaign_id"],
        },
    },
    {
        "name": "meta_list_adsets",
        "description": "List ad sets, optionally filtered to one campaign.",
        "input_schema": {
            "type": "object",
            "properties": {"campaign_id": {**_ID, "description": "Optional: only ad sets in this campaign"}},
        },
    },
    {
        "name": "meta_get_adset",
        "description": "Get one ad set by id.",
        "input_schema": {"type": "object", "properties": {"adset_id": _ID}, "required": ["adset_id"]},
    },
    {
        "name": "meta_list_ads",
        "description": "List ads, optionally filtered to one ad set.",
        "input_schema": {
            "type": "object",
            "properties": {"adset_id": {**_ID, "description": "Optional: only ads in this ad set"}},
        },
    },
    {
        "name": "meta_get_ad",
        "description": "Get one ad by id.",
        "input_schema": {"type": "object", "properties": {"ad_id": _ID}, "required": ["ad_id"]},
    },
    {
        "name": "meta_list_creatives",
        "description": "List all ad creatives in the account, with how many ads use each.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "meta_get_creative",
        "description": "Get one ad creative by id.",
        "input_schema": {
            "type": "object",
            "properties": {"creative_id": _ID},
            "required": ["creative_id"],
        },
    },
    {
        "name": "meta_get_account_insights",
        "description": "Account-level spend/impressions/clicks/purchases/CPA/ROAS for a date preset.",
        "input_schema": {"type": "object", "properties": _DATE_PRESET_PROP},
    },
    {
        "name": "meta_get_campaign_insights",
        "description": "Per-campaign spend/impressions/clicks/purchases/CPA/ROAS breakdown for a date preset.",
        "input_schema": {"type": "object", "properties": _DATE_PRESET_PROP},
    },
    {
        "name": "ga4_run_report",
        "description": "Run an arbitrary GA4 report with the given dimensions and metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dimensions": {"type": "array", "items": {"type": "string"}, "description": "GA4 dimension names"},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "GA4 metric names"},
                **_DATE_RANGE_PROPS,
            },
            "required": ["dimensions", "metrics"],
        },
    },
    {
        "name": "ga4_landing_page_report",
        "description": "GA4 sessions/users/keyEvents/revenue by landing page and source/medium.",
        "input_schema": {"type": "object", "properties": _DATE_RANGE_PROPS},
    },
    {
        "name": "ga4_campaign_report",
        "description": "GA4 sessions/users/keyEvents/revenue by campaign name and source/medium.",
        "input_schema": {"type": "object", "properties": _DATE_RANGE_PROPS},
    },
    {
        "name": "ga4_traffic_source_report",
        "description": "GA4 sessions/users/newUsers by source/medium.",
        "input_schema": {"type": "object", "properties": _DATE_RANGE_PROPS},
    },
    {
        "name": "ga4_conversion_report",
        "description": "GA4 eventCount/keyEvents by event name.",
        "input_schema": {"type": "object", "properties": _DATE_RANGE_PROPS},
    },
    {
        "name": "ga4_revenue_report",
        "description": "GA4 transactions/totalRevenue/purchaseRevenue by source/medium.",
        "input_schema": {"type": "object", "properties": _DATE_RANGE_PROPS},
    },
    {
        "name": "ga4_realtime_report",
        "description": "GA4 active users right now, by screen name and device category.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "ga4_property_info",
        "description": "GA4 property display name, timezone, and currency.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "analytics_correlate_campaigns",
        "description": (
            "Join Meta campaign spend/purchases with GA4 sessions/keyEvents/revenue for the same "
            "campaign id, kept side by side (never blended into one number)."
        ),
        "input_schema": {"type": "object", "properties": {**_DATE_PRESET_PROP, **_DATE_RANGE_PROPS}},
    },
    {
        "name": "woo_orders_summary",
        "description": (
            "Real completed-order revenue and count from the connected WooCommerce store for a date "
            "preset — the most trustworthy revenue number available (a paid order, unlike Meta/GA4 "
            "pixel-based purchase counts, can't be inflated by overlapping action_types or missed by "
            "iOS tracking restrictions). attributed_order_count is how many of those orders carry UTM "
            "campaign attribution and could in principle be matched to a specific Meta campaign."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date_preset": {
                    "type": "string",
                    "description": "One of: today, yesterday, last_7d, last_30d",
                }
            },
        },
    },
    {
        "name": "meta_create_campaign",
        "description": (
            "Create a new campaign. ALWAYS created PAUSED regardless of mode — resuming is a separate "
            "explicit action. Subject to the max-new-campaigns-per-day and max-campaign-budget ceilings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "objective": {"type": "string", "description": "e.g. OUTCOME_SALES, OUTCOME_LEADS"},
                "daily_budget_cents": {"type": "integer", "description": "Daily budget in cents (paise)"},
            },
            "required": ["name", "objective", "daily_budget_cents"],
        },
    },
    {
        "name": "meta_update_campaign_budget",
        "description": "Change a campaign's daily budget. Subject to budget ceiling and max-increase-% checks.",
        "input_schema": {
            "type": "object",
            "properties": {"campaign_id": _ID, "daily_budget_cents": {"type": "integer"}},
            "required": ["campaign_id", "daily_budget_cents"],
        },
    },
    {
        "name": "meta_pause_campaign",
        "description": "Pause a campaign.",
        "input_schema": {"type": "object", "properties": {"campaign_id": _ID}, "required": ["campaign_id"]},
    },
    {
        "name": "meta_resume_campaign",
        "description": "Resume (activate) a paused campaign. Treated as spend-increasing.",
        "input_schema": {"type": "object", "properties": {"campaign_id": _ID}, "required": ["campaign_id"]},
    },
    {
        "name": "meta_duplicate_campaign",
        "description": "Duplicate a campaign shell (name/objective/budget only, starts PAUSED). Does not copy ad sets/ads/creatives.",
        "input_schema": {
            "type": "object",
            "properties": {"campaign_id": _ID, "name_suffix": {"type": "string"}},
            "required": ["campaign_id"],
        },
    },
    {
        "name": "meta_update_adset_budget",
        "description": "Change an ad set's daily budget. Subject to budget ceiling and max-increase-% checks.",
        "input_schema": {
            "type": "object",
            "properties": {"adset_id": _ID, "daily_budget_cents": {"type": "integer"}},
            "required": ["adset_id", "daily_budget_cents"],
        },
    },
    {
        "name": "meta_pause_adset",
        "description": "Pause an ad set.",
        "input_schema": {"type": "object", "properties": {"adset_id": _ID}, "required": ["adset_id"]},
    },
    {
        "name": "meta_resume_adset",
        "description": "Resume (activate) a paused ad set. Treated as spend-increasing.",
        "input_schema": {"type": "object", "properties": {"adset_id": _ID}, "required": ["adset_id"]},
    },
    {
        "name": "meta_pause_ad",
        "description": "Pause an ad.",
        "input_schema": {"type": "object", "properties": {"ad_id": _ID}, "required": ["ad_id"]},
    },
    {
        "name": "meta_resume_ad",
        "description": "Resume (activate) a paused ad. Treated as spend-increasing.",
        "input_schema": {"type": "object", "properties": {"ad_id": _ID}, "required": ["ad_id"]},
    },
    {
        "name": "meta_create_ad",
        "description": (
            "Create a new ad in an ad set using an existing creative. ALWAYS created PAUSED. "
            "Subject to the max-ads-per-campaign ceiling."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "adset_id": _ID,
                "creative_id": {**_ID, "description": "Existing creative id — create one first if needed"},
            },
            "required": ["name", "adset_id", "creative_id"],
        },
    },
    {
        "name": "meta_create_creative",
        "description": (
            "Create an ad creative from an existing uploaded image_hash or video_id (upload images/videos "
            "from the Creatives page first — this tool cannot upload binary assets itself)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "message": {"type": "string", "description": "Primary ad text"},
                "link": {"type": "string"},
                "headline": {"type": "string"},
                "call_to_action": {"type": "string", "description": "e.g. LEARN_MORE, SHOP_NOW, SIGN_UP"},
                "image_hash": {"type": "string", "description": "Required if no video_id"},
                "video_id": {"type": "string", "description": "Required if no image_hash"},
            },
            "required": ["name", "message", "link", "headline"],
        },
    },
]
