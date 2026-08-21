"""Deterministic metric calculations — never delegated to Claude. Meta's
insights API reports conversions inside generic `actions`/`action_values`
arrays keyed by action_type — and those action_types OVERLAP rather than
partition the data: a single web-pixel purchase is typically reported
under BOTH "purchase" and "omni_purchase" (Meta's deduplicated
cross-channel aggregate, which already includes what "purchase" counts).
Summing every matching action_type therefore double-counts the same
conversion. The fix is to pick exactly one action_type per event, in
priority order, never sum across types — confirmed against a real account
where this bug was inflating today's purchases/revenue by exactly 2x
versus Meta's own Ads Manager numbers for the same date range."""

_PURCHASE_ACTION_PRIORITY = ("omni_purchase", "purchase")


def _extract_single_action(entries: list[dict] | None, action_types: tuple[str, ...]) -> float:
    if not entries:
        return 0.0
    totals: dict[str, float] = {}
    for entry in entries:
        action_type = entry.get("action_type")
        if action_type is None:
            continue
        totals[action_type] = totals.get(action_type, 0.0) + float(entry.get("value", 0))
    for action_type in action_types:
        if action_type in totals:
            return totals[action_type]
    return 0.0


def extract_purchases(actions: list[dict] | None) -> float:
    return _extract_single_action(actions, _PURCHASE_ACTION_PRIORITY)


def extract_purchase_value(action_values: list[dict] | None) -> float:
    return _extract_single_action(action_values, _PURCHASE_ACTION_PRIORITY)


def calc_cpa(spend: float, purchases: float) -> float | None:
    if purchases <= 0:
        return None
    return spend / purchases


def calc_roas(purchase_value: float, spend: float) -> float | None:
    if spend <= 0:
        return None
    return purchase_value / spend


def calc_ctr(clicks: float, impressions: float) -> float | None:
    if impressions <= 0:
        return None
    return (clicks / impressions) * 100


def calc_cpc(spend: float, clicks: float) -> float | None:
    if clicks <= 0:
        return None
    return spend / clicks


def calc_cpm(spend: float, impressions: float) -> float | None:
    if impressions <= 0:
        return None
    return (spend / impressions) * 1000
