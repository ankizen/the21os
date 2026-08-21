import json

import pytest
from facebook_business.exceptions import FacebookRequestError

from the21os.meta.client import _call_with_retry


def _rate_limit_error() -> FacebookRequestError:
    body = json.dumps({"error": {"code": 4, "message": "rate limited"}})
    return FacebookRequestError(
        message="rate limited", request_context={}, http_status=400, http_headers={}, body=body
    )


def _permission_error() -> FacebookRequestError:
    body = json.dumps({"error": {"code": 10, "message": "permission denied"}})
    return FacebookRequestError(
        message="permission denied", request_context={}, http_status=403, http_headers={}, body=body
    )


def test_retries_on_rate_limit_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("the21os.meta.client.time.sleep", lambda _seconds: None)
    calls = {"count": 0}

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise _rate_limit_error()
        return "ok"

    assert _call_with_retry(flaky) == "ok"
    assert calls["count"] == 3


def test_gives_up_after_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("the21os.meta.client.time.sleep", lambda _seconds: None)
    calls = {"count": 0}

    def always_rate_limited() -> str:
        calls["count"] += 1
        raise _rate_limit_error()

    with pytest.raises(FacebookRequestError):
        _call_with_retry(always_rate_limited)
    assert calls["count"] == 3  # _MAX_RETRIES, no more


def test_non_rate_limit_error_raises_immediately() -> None:
    calls = {"count": 0}

    def denied() -> str:
        calls["count"] += 1
        raise _permission_error()

    with pytest.raises(FacebookRequestError):
        _call_with_retry(denied)
    assert calls["count"] == 1  # no retry for a non-rate-limit error
