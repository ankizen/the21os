import uuid
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from the21os.audit.service import write_audit_log
from the21os.auth.dependencies import get_current_user
from the21os.db.base import get_db
from the21os.db.models import User, WordPressConnection
from the21os.wordpress.client import WordPressNotConfigured, check_woo_connection, check_wp_connection
from the21os.wordpress.orders import date_preset_range, list_orders, orders_summary

router = APIRouter(
    prefix="/api/integrations/wordpress", tags=["wordpress"], dependencies=[Depends(get_current_user)]
)

T = TypeVar("T")


class WordPressStatus(BaseModel):
    configured: bool
    site_url: str | None = None
    wp_connected: bool | None = None
    wp_user: str | None = None
    wp_error: str | None = None
    woo_connected: bool | None = None
    woo_order_count: int | None = None
    woo_error: str | None = None


async def _get_or_create(db: AsyncSession) -> WordPressConnection:
    row = await db.get(WordPressConnection, 1)
    if row is None:
        row = WordPressConnection(id=1)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


async def _status(db: AsyncSession) -> WordPressStatus:
    row = await _get_or_create(db)
    if not row.site_url:
        return WordPressStatus(configured=False)

    status = WordPressStatus(configured=True, site_url=row.site_url)

    try:
        wp_info = await check_wp_connection(row)
        status.wp_connected = True
        status.wp_user = wp_info["name"]
    except WordPressNotConfigured as e:
        status.wp_connected = False
        status.wp_error = str(e)
    except httpx.HTTPError as e:
        status.wp_connected = False
        status.wp_error = str(e)

    try:
        woo_info = await check_woo_connection(row)
        status.woo_connected = True
        status.woo_order_count = woo_info["order_count"]
    except WordPressNotConfigured as e:
        status.woo_connected = False
        status.woo_error = str(e)
    except httpx.HTTPError as e:
        status.woo_connected = False
        status.woo_error = str(e)

    return status


@router.get("/status", response_model=WordPressStatus)
async def wordpress_status(db: AsyncSession = Depends(get_db)) -> WordPressStatus:
    return await _status(db)


class WordPressConnectRequest(BaseModel):
    site_url: str
    app_username: str
    app_password: str
    woo_consumer_key: str
    woo_consumer_secret: str


@router.put("", response_model=WordPressStatus)
async def connect_wordpress(
    body: WordPressConnectRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WordPressStatus:
    site_url = body.site_url.strip().rstrip("/")
    if not site_url.startswith("https://"):
        raise HTTPException(status_code=422, detail="Site URL must start with https://")

    row = await _get_or_create(db)
    row.site_url = site_url
    row.app_username = body.app_username.strip()
    row.app_password = body.app_password.strip()
    row.woo_consumer_key = body.woo_consumer_key.strip()
    row.woo_consumer_secret = body.woo_consumer_secret.strip()
    await db.commit()

    await write_audit_log(
        db,
        request_id=str(uuid.uuid4()),
        actor=user.email,
        source="rest_api",
        action="wordpress.connect",
        entity="wordpress_connection",
        entity_id="1",
        params=body.model_dump(),  # app_password / woo_consumer_key / woo_consumer_secret auto-redacted
        success=True,
        decision_reason=f"WordPress connection updated ({site_url})",
    )
    return await _status(db)


class OrderSummary(BaseModel):
    date_preset: str
    order_count: int
    revenue: float
    currency: str | None
    attributed_order_count: int


class OrderEntry(BaseModel):
    id: int
    status: str
    date_created: str | None
    total: float
    currency: str | None
    utm_campaign: str | None
    utm_source: str | None
    source_type: str | None


async def _run_orders(fn: Callable[[], Awaitable[T]]) -> T:
    try:
        return await fn()
    except WordPressNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"WooCommerce API request failed: {e}") from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("/orders/summary", response_model=OrderSummary)
async def orders_summary_endpoint(
    date_preset: str = Query(default="today"), db: AsyncSession = Depends(get_db)
) -> OrderSummary:
    row = await _get_or_create(db)
    return await _run_orders(lambda: orders_summary(row, date_preset))


@router.get("/orders/recent", response_model=list[OrderEntry])
async def recent_orders(
    date_preset: str = Query(default="today"), db: AsyncSession = Depends(get_db)
) -> list[OrderEntry]:
    row = await _get_or_create(db)

    async def _fetch():
        after, before = date_preset_range(date_preset)
        return await list_orders(row, after, before)

    return await _run_orders(_fetch)
