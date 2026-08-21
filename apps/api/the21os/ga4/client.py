import asyncio
import json
import threading
from collections.abc import Callable
from typing import TypeVar

from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account

from the21os.config import get_settings

T = TypeVar("T")

_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

_lock = threading.Lock()
_data_client: BetaAnalyticsDataClient | None = None
_admin_client: AnalyticsAdminServiceClient | None = None


class GA4NotConfigured(RuntimeError):
    """Raised when GA4 credentials aren't set but a caller tries to use them."""


def _credentials() -> service_account.Credentials:
    settings = get_settings()
    if not settings.google_service_account_json:
        raise GA4NotConfigured("GOOGLE_SERVICE_ACCOUNT_JSON is not configured")
    info = json.loads(settings.google_service_account_json)
    return service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)


def get_data_client() -> BetaAnalyticsDataClient:
    global _data_client
    if _data_client is None:
        with _lock:
            if _data_client is None:
                _data_client = BetaAnalyticsDataClient(credentials=_credentials())
    return _data_client


def get_admin_client() -> AnalyticsAdminServiceClient:
    global _admin_client
    if _admin_client is None:
        with _lock:
            if _admin_client is None:
                _admin_client = AnalyticsAdminServiceClient(credentials=_credentials())
    return _admin_client


def property_path(property_id: str | None = None) -> str:
    settings = get_settings()
    pid = property_id or settings.ga4_property_id
    if not pid:
        raise GA4NotConfigured("GA4_PROPERTY_ID is not configured")
    return f"properties/{pid}"


async def call_ga4(fn: Callable[[], T]) -> T:
    """Run a synchronous GA4 SDK call off the event loop. The GAPIC clients
    already retry transient/rate-limit errors internally (default retry
    policy on every generated method) — no need to duplicate that here."""
    return await asyncio.to_thread(fn)
