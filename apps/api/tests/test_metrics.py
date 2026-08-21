from the21secrets.core.metrics import (
    calc_cpa,
    calc_cpc,
    calc_cpm,
    calc_ctr,
    calc_roas,
    extract_purchase_value,
    extract_purchases,
)


def test_extract_purchases_sums_matching_action_types() -> None:
    actions = [
        {"action_type": "purchase", "value": "3"},
        {"action_type": "omni_purchase", "value": "2"},
        {"action_type": "link_click", "value": "50"},
    ]
    assert extract_purchases(actions) == 5.0


def test_extract_purchases_handles_none_and_empty() -> None:
    assert extract_purchases(None) == 0.0
    assert extract_purchases([]) == 0.0


def test_extract_purchase_value() -> None:
    action_values = [{"action_type": "purchase", "value": "199.98"}]
    assert extract_purchase_value(action_values) == 199.98


def test_calc_cpa() -> None:
    assert calc_cpa(spend=100.0, purchases=4.0) == 25.0
    assert calc_cpa(spend=100.0, purchases=0) is None


def test_calc_roas() -> None:
    assert calc_roas(purchase_value=300.0, spend=100.0) == 3.0
    assert calc_roas(purchase_value=300.0, spend=0) is None


def test_calc_ctr() -> None:
    assert calc_ctr(clicks=5.0, impressions=1000.0) == 0.5
    assert calc_ctr(clicks=5.0, impressions=0) is None


def test_calc_cpc() -> None:
    assert calc_cpc(spend=50.0, clicks=25.0) == 2.0
    assert calc_cpc(spend=50.0, clicks=0) is None


def test_calc_cpm() -> None:
    assert calc_cpm(spend=10.0, impressions=2000.0) == 5.0
    assert calc_cpm(spend=10.0, impressions=0) is None
