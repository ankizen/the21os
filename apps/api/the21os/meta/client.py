import asyncio
import logging
import threading
import time
from collections.abc import Callable
from typing import TypeVar

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

from the21os.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Meta's rate-limit / throttling error codes (Graph API + Marketing API BUC
# limits). Retried with backoff; anything else is raised straight through.
_RATE_LIMIT_CODES = {4, 17, 32, 613}
_MAX_RETRIES = 3

_init_lock = threading.Lock()
_initialized = False


class MetaNotConfigured(RuntimeError):
    """Raised when Meta credentials aren't set but a caller tries to use them."""


def ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        settings = get_settings()
        if not (settings.meta_app_id and settings.meta_app_secret and settings.meta_access_token):
            raise MetaNotConfigured("META_APP_ID / META_APP_SECRET / META_ACCESS_TOKEN are not configured")
        # FacebookAdsApi.init computes appsecret_proof automatically for
        # every request once app_secret is provided — no manual HMAC needed.
        FacebookAdsApi.init(
            app_id=settings.meta_app_id,
            app_secret=settings.meta_app_secret,
            access_token=settings.meta_access_token,
            api_version=settings.meta_api_version,
        )
        _initialized = True


def default_account_id() -> str:
    settings = get_settings()
    if not settings.meta_default_ad_account_id:
        raise MetaNotConfigured("META_DEFAULT_AD_ACCOUNT_ID is not configured")
    return settings.meta_default_ad_account_id


def get_account(account_id: str | None = None) -> AdAccount:
    ensure_initialized()
    return AdAccount(account_id or default_account_id())


def _call_with_retry(fn: Callable[[], T]) -> T:
    last_error: FacebookRequestError | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return fn()
        except FacebookRequestError as e:
            last_error = e
            if e.api_error_code() in _RATE_LIMIT_CODES and attempt < _MAX_RETRIES - 1:
                wait = 2**attempt
                logger.warning("Meta API rate limited (code %s), retrying in %ss", e.api_error_code(), wait)
                time.sleep(wait)
                continue
            raise
    assert last_error is not None  # pragma: no cover — loop always returns or raises
    raise last_error


async def call_meta(fn: Callable[[], T]) -> T:
    """Run a synchronous facebook-business SDK call off the event loop, with
    retry-with-backoff on Meta's rate-limit error codes."""
    ensure_initialized()
    return await asyncio.to_thread(_call_with_retry, fn)
