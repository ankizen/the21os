from datetime import datetime

import pytest

from the21os.wordpress.orders import _extract_attribution, _to_order_summary, date_preset_range


def test_date_preset_range_today_starts_at_midnight() -> None:
    start, end = date_preset_range("today")
    assert datetime.fromisoformat(start).time().hour == 0
    assert datetime.fromisoformat(end) > datetime.fromisoformat(start)


def test_date_preset_range_yesterday_is_a_full_day_before_today() -> None:
    today_start, _ = date_preset_range("today")
    yesterday_start, yesterday_end = date_preset_range("yesterday")
    assert yesterday_end == today_start
    assert datetime.fromisoformat(yesterday_start) < datetime.fromisoformat(yesterday_end)


def test_date_preset_range_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError):
        date_preset_range("last_year")


def test_extract_attribution_reads_order_attribution_meta() -> None:
    meta_data = [
        {"key": "_wc_order_attribution_utm_campaign", "value": "120212345"},
        {"key": "_wc_order_attribution_utm_source", "value": "facebook"},
        {"key": "_wc_order_attribution_source_type", "value": "paid"},
        {"key": "_billing_address_index", "value": "unrelated"},
    ]
    attribution = _extract_attribution(meta_data)
    assert attribution == {
        "utm_campaign": "120212345",
        "utm_source": "facebook",
        "source_type": "paid",
    }


def test_extract_attribution_missing_meta_returns_none_not_error() -> None:
    assert _extract_attribution([]) == {"utm_campaign": None, "utm_source": None, "source_type": None}


def test_to_order_summary_never_includes_billing_or_shipping() -> None:
    raw_order = {
        "id": 42,
        "status": "completed",
        "date_created": "2026-08-21T10:00:00",
        "total": "449.00",
        "currency": "INR",
        "billing": {"email": "customer@example.com", "phone": "9999999999"},
        "shipping": {"address_1": "123 Somewhere"},
        "meta_data": [{"key": "_wc_order_attribution_utm_campaign", "value": "120212345"}],
    }
    summary = _to_order_summary(raw_order)
    assert summary == {
        "id": 42,
        "status": "completed",
        "date_created": "2026-08-21T10:00:00",
        "total": 449.0,
        "currency": "INR",
        "utm_campaign": "120212345",
        "utm_source": None,
        "source_type": None,
    }
    assert "billing" not in summary
    assert "shipping" not in summary
