from the21os.audit.redact import REDACTED, redact


def test_redacts_secret_shaped_keys() -> None:
    out = redact({"access_token": "eaa123", "api_key": "sk-abc", "password": "hunter2"})
    assert out == {"access_token": REDACTED, "api_key": REDACTED, "password": REDACTED}


def test_keeps_non_secret_keys() -> None:
    out = redact({"campaign_id": "123", "budget_cents": 5000})
    assert out == {"campaign_id": "123", "budget_cents": 5000}


def test_redacts_any_field_name_containing_key() -> None:
    # Broad "key" match on purpose — catches future *_key fields (e.g.
    # woo_consumer_key) without needing every new secret name added by hand.
    out = redact({"woo_consumer_key": "ck_abc", "woo_consumer_secret": "cs_abc", "site_url": "https://x.com"})
    assert out == {"woo_consumer_key": REDACTED, "woo_consumer_secret": REDACTED, "site_url": "https://x.com"}


def test_redacts_nested_and_list_values() -> None:
    out = redact(
        {"user": {"email": "a@b.com", "meta_access_token": "eaa123"}, "items": [{"totp_secret": "x"}]}
    )
    assert out["user"]["email"] == "a@b.com"
    assert out["user"]["meta_access_token"] == REDACTED
    assert out["items"][0]["totp_secret"] == REDACTED
