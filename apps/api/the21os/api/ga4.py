from collections.abc import Awaitable, Callable
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query
from google.api_core.exceptions import GoogleAPICallError

from the21os.auth.dependencies import get_current_user
from the21os.ga4 import accounts, realtime, reports
from the21os.ga4.client import GA4NotConfigured
from the21os.ga4.models import PropertyInfo, Report

router = APIRouter(prefix="/api/ga4", tags=["ga4"], dependencies=[Depends(get_current_user)])

T = TypeVar("T")


async def _run(fn: Callable[[], Awaitable[T]]) -> T:
    try:
        return await fn()
    except GA4NotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502, detail=str(e.message) or "GA4 API request failed") from e


@router.get("/property", response_model=PropertyInfo)
async def get_property() -> PropertyInfo:
    return await _run(accounts.get_property_info)


@router.get("/realtime", response_model=Report)
async def get_realtime() -> Report:
    return await _run(realtime.realtime_report)


@router.get("/reports/landing-pages", response_model=Report)
async def get_landing_pages(
    start_date: str = Query(default="28daysAgo"), end_date: str = Query(default="today")
) -> Report:
    return await _run(lambda: reports.landing_page_report(start_date, end_date))


@router.get("/reports/campaigns", response_model=Report)
async def get_campaign_report(
    start_date: str = Query(default="28daysAgo"), end_date: str = Query(default="today")
) -> Report:
    return await _run(lambda: reports.campaign_report(start_date, end_date))


@router.get("/reports/traffic-sources", response_model=Report)
async def get_traffic_sources(
    start_date: str = Query(default="28daysAgo"), end_date: str = Query(default="today")
) -> Report:
    return await _run(lambda: reports.traffic_source_report(start_date, end_date))


@router.get("/reports/conversions", response_model=Report)
async def get_conversions(
    start_date: str = Query(default="28daysAgo"), end_date: str = Query(default="today")
) -> Report:
    return await _run(lambda: reports.conversion_report(start_date, end_date))


@router.get("/reports/revenue", response_model=Report)
async def get_revenue(
    start_date: str = Query(default="28daysAgo"), end_date: str = Query(default="today")
) -> Report:
    return await _run(lambda: reports.revenue_report(start_date, end_date))
