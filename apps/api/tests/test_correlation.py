from the21os.core.correlation import correlate_campaigns


def test_joins_matching_campaign_ids() -> None:
    meta_rows = [
        {
            "campaign_id": "123",
            "campaign_name": "Summer Sale",
            "spend": 100.0,
            "purchases": 5.0,
            "purchase_value": 500.0,
        }
    ]
    ga4_rows = [{"campaign_id": "123", "sessions": 50.0, "users": 40.0, "key_events": 4.0, "revenue": 450.0}]

    result = correlate_campaigns(meta_rows, ga4_rows)

    assert len(result) == 1
    row = result[0]
    assert row["campaign_id"] == "123"
    assert row["meta_spend"] == 100.0
    assert row["ga4_sessions"] == 50.0
    assert row["has_ga4_data"] is True
    assert row["conversion_discrepancy"] == 1.0  # 5 Meta purchases vs 4 GA4 key events


def test_sums_multiple_ga4_rows_for_same_campaign() -> None:
    # GA4's campaign_report breaks out by source/medium too — two rows per
    # campaign_id is the normal case, not an edge case.
    meta_rows = [
        {"campaign_id": "123", "campaign_name": "X", "spend": 0.0, "purchases": 0.0, "purchase_value": 0.0}
    ]
    ga4_rows = [
        {"campaign_id": "123", "sessions": 30.0, "users": 25.0, "key_events": 2.0, "revenue": 100.0},
        {"campaign_id": "123", "sessions": 20.0, "users": 15.0, "key_events": 1.0, "revenue": 50.0},
    ]

    result = correlate_campaigns(meta_rows, ga4_rows)

    assert result[0]["ga4_sessions"] == 50.0
    assert result[0]["ga4_key_events"] == 3.0
    assert result[0]["ga4_revenue"] == 150.0


def test_campaign_with_no_ga4_data_is_labeled_not_zero_filled_lie() -> None:
    meta_rows = [
        {
            "campaign_id": "999",
            "campaign_name": "No UTM traffic",
            "spend": 50.0,
            "purchases": 1.0,
            "purchase_value": 100.0,
        }
    ]

    result = correlate_campaigns(meta_rows, ga4_rows=[])

    assert result[0]["has_ga4_data"] is False
    assert result[0]["ga4_sessions"] == 0.0
    # No fabricated discrepancy when there's genuinely no GA4 side to compare.
    assert result[0]["conversion_discrepancy"] is None


def test_woo_rows_join_by_campaign_id_and_sum_order_count() -> None:
    meta_rows = [
        {
            "campaign_id": "123",
            "campaign_name": "Summer Sale",
            "spend": 100.0,
            "purchases": 5.0,
            "purchase_value": 500.0,
        }
    ]
    woo_rows = [
        {"campaign_id": "123", "revenue": 449.0, "order_count": 1},
        {"campaign_id": "123", "revenue": 449.0, "order_count": 1},
    ]

    result = correlate_campaigns(meta_rows, ga4_rows=[], woo_rows=woo_rows)

    assert result[0]["woo_revenue"] == 898.0
    assert result[0]["woo_order_count"] == 2
    assert result[0]["has_woo_data"] is True


def test_woo_rows_defaults_to_no_data_not_zero_revenue() -> None:
    meta_rows = [
        {"campaign_id": "999", "campaign_name": "X", "spend": 50.0, "purchases": 1.0, "purchase_value": 100.0}
    ]

    result = correlate_campaigns(meta_rows, ga4_rows=[], woo_rows=None)

    assert result[0]["has_woo_data"] is False
    assert result[0]["woo_revenue"] == 0.0
    assert result[0]["woo_order_count"] == 0.0


def test_ga4_campaign_with_no_meta_row_is_simply_absent() -> None:
    # Organic/other traffic tagged with a campaign-like UTM but no matching
    # Meta campaign shouldn't silently invent a Meta-side row.
    ga4_rows = [
        {
            "campaign_id": "not-a-meta-campaign",
            "sessions": 10.0,
            "users": 10.0,
            "key_events": 0.0,
            "revenue": 0.0,
        }
    ]

    result = correlate_campaigns(meta_rows=[], ga4_rows=ga4_rows)

    assert result == []
