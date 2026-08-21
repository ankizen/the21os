from the21secrets.audit.redact import REDACTED, redact


def test_redacts_secret_shaped_keys() -> None:
    out = redact({"access_token": "eaa123", "api_key": "sk-abc", "password": "hunter2"})
    assert out == {"access_token": REDACTED, "api_key": REDACTED, "password": REDACTED}


def test_keeps_non_secret_keys() -> None:
    out = redact({"campaign_id": "123", "budget_cents": 5000})
    assert out == {"campaign_id": "123", "budget_cents": 5000}


def test_redacts_nested_and_list_values() -> None:
    out = redact(
        {"user": {"email": "a@b.com", "meta_access_token": "eaa123"}, "items": [{"totp_secret": "x"}]}
    )
    assert out["user"]["email"] == "a@b.com"
    assert out["user"]["meta_access_token"] == REDACTED
    assert out["items"][0]["totp_secret"] == REDACTED
