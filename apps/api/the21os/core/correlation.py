"""Joins Meta campaign performance with GA4 session/conversion data by
campaign ID. Real correlation, not fabricated attribution: this only works
because this account's UTM campaign parameter happens to be the literal
Meta campaign ID (confirmed against the real property — GA4's
sessionCampaignName dimension returns the same numeric string as Meta's
campaign id). Every row keeps both sources' numbers separately labeled,
never blended into one "true" figure — master prompt SS15 is explicit that
Meta-reported and GA4-reported conversions must stay distinguishable,
including when they disagree."""

from collections import defaultdict


def correlate_campaigns(meta_rows: list[dict], ga4_rows: list[dict]) -> list[dict]:
    """
    meta_rows: [{"campaign_id", "campaign_name", "spend", "purchases", "purchase_value"}]
    ga4_rows:  [{"campaign_id", "sessions", "users", "key_events", "revenue"}]
        (already aggregated across source/medium per campaign_id by the caller,
        or left un-aggregated — this function sums duplicates either way.)
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

    result = []
    for m in meta_rows:
        g = ga4_by_campaign.get(m["campaign_id"])
        has_ga4_data = g is not None
        g = g or {"sessions": 0.0, "users": 0.0, "key_events": 0.0, "revenue": 0.0}
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
            }
        )
    return result
