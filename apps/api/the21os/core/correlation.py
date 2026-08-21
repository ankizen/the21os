"""Joins Meta campaign performance with GA4 session/conversion data, and
optionally real WooCommerce order data, by campaign ID. Real correlation,
not fabricated attribution: this only works because this account's UTM
campaign parameter happens to be the literal Meta campaign ID (confirmed
against the real property — GA4's sessionCampaignName dimension and
WooCommerce's Order Attribution utm_campaign meta both return the same
numeric string as Meta's campaign id). Every row keeps every source's
numbers separately labeled, never blended into one "true" figure — master
prompt SS15 is explicit that Meta-reported and GA4-reported conversions
must stay distinguishable, including when they disagree. WooCommerce's
numbers are the odd one out in a good way: a completed order isn't
pixel/tag-based, so it can't be inflated or missed the way Meta's/GA4's
can."""

from collections import defaultdict


def correlate_campaigns(
    meta_rows: list[dict], ga4_rows: list[dict], woo_rows: list[dict] | None = None
) -> list[dict]:
    """
    meta_rows: [{"campaign_id", "campaign_name", "spend", "purchases", "purchase_value"}]
    ga4_rows:  [{"campaign_id", "sessions", "users", "key_events", "revenue"}]
    woo_rows:  [{"campaign_id", "revenue", "order_count"}] — real completed WooCommerce
        orders with UTM campaign attribution. Optional: None/[] means WooCommerce isn't
        connected or has no attributed orders in range, not that revenue was zero —
        has_woo_data distinguishes the two, same as has_ga4_data already does.
        (all three are already aggregated across source/medium per campaign_id by the
        caller, or left un-aggregated — this function sums duplicates either way.)
    """
    ga4_by_campaign: dict[str, dict[str, float]] = defaultdict(
        lambda: {"sessions": 0.0, "users": 0.0, "key_events": 0.0, "revenue": 0.0}
    )
    for row in ga4_rows:
        agg = ga4_by_campaign[row["campaign_id"]]
        agg["sessions"] += row.get("sessions", 0.0)
        agg["users"] += row.get("users", 0.0)
        agg["key_events"] += row.get("key_events", 0.0)
        agg["revenue"] += row.get("revenue", 0.0)

    woo_by_campaign: dict[str, dict[str, float]] = defaultdict(lambda: {"revenue": 0.0, "order_count": 0.0})
    for row in woo_rows or []:
        agg = woo_by_campaign[row["campaign_id"]]
        agg["revenue"] += row.get("revenue", 0.0)
        agg["order_count"] += row.get("order_count", 0.0)

    result = []
    for m in meta_rows:
        g = ga4_by_campaign.get(m["campaign_id"])
        has_ga4_data = g is not None
        g = g or {"sessions": 0.0, "users": 0.0, "key_events": 0.0, "revenue": 0.0}

        w = woo_by_campaign.get(m["campaign_id"])
        has_woo_data = w is not None
        w = w or {"revenue": 0.0, "order_count": 0.0}

        result.append(
            {
                "campaign_id": m["campaign_id"],
                "campaign_name": m["campaign_name"],
                "meta_spend": m.get("spend", 0.0),
                "meta_purchases": m.get("purchases", 0.0),
                "meta_purchase_value": m.get("purchase_value", 0.0),
                "ga4_sessions": g["sessions"],
                "ga4_users": g["users"],
                "ga4_key_events": g["key_events"],
                "ga4_revenue": g["revenue"],
                "has_ga4_data": has_ga4_data,
                "conversion_discrepancy": m.get("purchases", 0.0) - g["key_events"] if has_ga4_data else None,
                "woo_revenue": w["revenue"],
                "woo_order_count": w["order_count"],
                "has_woo_data": has_woo_data,
            }
        )
    return result
