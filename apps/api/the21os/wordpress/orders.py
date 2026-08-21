"""Order data from the connected WooCommerce store — a third, ground-truth
revenue source alongside Meta-reported and GA4-reported numbers (per
core/correlation.py's philosophy: never blend sources, always keep them
separately labeled). A completed order is unambiguous in a way pixel/tag
tracking is not — it can't be inflated by overlapping action_types or
missed by iOS tracking restrictions.

Only order-level facts are ever extracted here — never customer PII
(name/email/address/phone) from billing/shipping, per master prompt SS20."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from the21os.db.models import WordPressConnection
from the21os.wordpress.client import WordPressNotConfigured, woo_auth

_TIMEOUT = 20.0

# ponytail: hardcoded to the one store this system runs for (an Indian
# business — INR, IST). Make this a WordPressConnection column if a second
# store in another timezone is ever connected.
_STORE_TZ = ZoneInfo("Asia/Kolkata")

# WooCommerce's own reporting counts these as real revenue; "pending",
# "on-hold", "cancelled", "failed", "refunded" are deliberately excluded —
# an order isn't revenue until it's actually been paid for.
_COUNTED_STATUSES = ("completed", "processing")

_DATE_PRESET_DAYS = {"today": 0, "yesterday": 1, "last_7d": 7, "last_30d": 30}


def date_preset_range(date_preset: str) -> tuple[str, str]:
    if date_preset not in _DATE_PRESET_DAYS:
        raise ValueError(f"Unsupported date_preset {date_preset!r} (use one of {list(_DATE_PRESET_DAYS)})")
    now = datetime.now(_STORE_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days = _DATE_PRESET_DAYS[date_preset]
    if date_preset == "yesterday":
        return (today_start - timedelta(days=1)).isoformat(), today_start.isoformat()
    start = today_start - timedelta(days=days)
    return start.isoformat(), now.isoformat()


def _extract_attribution(meta_data: list[dict]) -> dict:
    """WooCommerce's built-in Order Attribution feature (core since 8.5)
    stores these as order meta if the checkout theme/plugin passes UTM
    params through. Empty values mean the store isn't populating them, not
    that the fields are missing/broken."""
    by_key = {m.get("key"): m.get("value") for m in meta_data if isinstance(m, dict)}
    return {
        "utm_campaign": by_key.get("_wc_order_attribution_utm_campaign"),
        "utm_source": by_key.get("_wc_order_attribution_utm_source"),
        "source_type": by_key.get("_wc_order_attribution_source_type"),
    }


def _to_order_summary(raw: dict) -> dict:
    return {
        "id": raw["id"],
        "status": raw["status"],
        "date_created": raw.get("date_created"),
        "total": float(raw.get("total") or 0),
        "currency": raw.get("currency"),
        **_extract_attribution(raw.get("meta_data") or []),
    }


async def list_orders(conn: WordPressConnection, after: str, before: str) -> list[dict]:
    """Orders created in [after, before) (ISO8601, store timezone), counted
    statuses only. Strips everything down to order-level facts — never
    billing/shipping PII."""
    if not (conn.site_url and conn.woo_consumer_key and conn.woo_consumer_secret):
        raise WordPressNotConfigured("WooCommerce Consumer Key/Secret not set")

    orders: list[dict] = []
    page = 1
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        while True:
            resp = await client.get(
                f"{conn.site_url}/wp-json/wc/v3/orders",
                params={
                    "after": after,
                    "before": before,
                    "status": ",".join(_COUNTED_STATUSES),
                    "per_page": 100,
                    "page": page,
                    "orderby": "date",
                    "order": "desc",
                },
                auth=woo_auth(conn),
            )
            resp.raise_for_status()
            batch = resp.json()
            orders.extend(_to_order_summary(o) for o in batch)
            if len(batch) < 100:
                break
            page += 1
    return orders


async def orders_summary(conn: WordPressConnection, date_preset: str) -> dict:
    after, before = date_preset_range(date_preset)
    orders = await list_orders(conn, after, before)
    revenue = sum(o["total"] for o in orders)
    currency = orders[0]["currency"] if orders else None
    attributed = sum(1 for o in orders if o["utm_campaign"])
    return {
        "date_preset": date_preset,
        "order_count": len(orders),
        "revenue": revenue,
        "currency": currency,
        "attributed_order_count": attributed,
    }
