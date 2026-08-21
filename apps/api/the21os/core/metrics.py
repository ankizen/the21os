"""Deterministic metric calculations — never delegated to Claude. Meta's
insights API reports conversions inside generic `actions`/`action_values`
arrays rather than dedicated fields, so extracting "purchases" needs a
lookup by action_type first."""

_PURCHASE_ACTION_TYPES = {"purchase", "omni_purchase"}


def extract_action_count(actions: list[dict] | None, action_types: set[str]) -> float:
    if not actions:
        return 0.0
    return sum(float(a["value"]) for a in actions if a.get("action_type") in action_types)


def extract_purchases(actions: list[dict] | None) -> float:
    return extract_action_count(actions, _PURCHASE_ACTION_TYPES)


def extract_purchase_value(action_values: list[dict] | None) -> float:
    return extract_action_count(action_values, _PURCHASE_ACTION_TYPES)


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
