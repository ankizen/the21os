from facebook_business.exceptions import FacebookRequestError
from fastapi import APIRouter, Depends, HTTPException, Query
from google.api_core.exceptions import GoogleAPICallError
from pydantic import BaseModel

from the21os.auth.dependencies import get_current_user
from the21os.core.correlation import correlate_campaigns
from the21os.ga4 import reports as ga4_reports
from the21os.ga4.client import GA4NotConfigured
from the21os.meta import insights as meta_insights
from the21os.meta.client import MetaNotConfigured

router = APIRouter(prefix="/api/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])


class CorrelationRow(BaseModel):
    campaign_id: str
    campaign_name: str
    meta_spend: float
    meta_purchases: float
    meta_purchase_value: float
    ga4_sessions: float
    ga4_users: float
    ga4_key_events: float
    ga4_revenue: float
    has_ga4_data: bool
    conversion_discrepancy: float | None


@router.get("/correlation", response_model=list[CorrelationRow])
async def get_correlation(
    date_preset: str = Query(default="last_30d"),
    start_date: str = Query(default="28daysAgo"),
    end_date: str = Query(default="today"),
) -> list[CorrelationRow]:
    """Meta campaign performance next to GA4 sessions/key events for the same
    campaign ID — never blended into one number, see core/correlation.py."""
    try:
        meta_data = await meta_insights.get_campaign_insights(date_preset=date_preset)
    except MetaNotConfigured as e:
        raise HTTPException(status_code=503, detail=f"Meta: {e}") from e
    except FacebookRequestError as e:
        raise HTTPException(status_code=502, detail=e.api_error_message() or "Meta API request failed") from e

    try:
        ga4_data = await ga4_reports.campaign_report(start_date=start_date, end_date=end_date)
    except GA4NotConfigured as e:
        raise HTTPException(status_code=503, detail=f"GA4: {e}") from e
    except GoogleAPICallError as e:
        raise HTTPException(status_code=502, detail=str(e.message) or "GA4 API request failed") from e

    meta_rows = [
        {
            "campaign_id": m.entity_id,
            "campaign_name": m.entity_name or m.entity_id,
            "spend": m.spend,
            "purchases": m.purchases,
            "purchase_value": m.purchase_value,
        }
        for m in meta_data
        if m.entity_id
    ]
    ga4_rows = [
        {
            "campaign_id": row.dimensions.get("sessionCampaignName", ""),
            "sessions": row.metrics.get("sessions", 0.0),
            "users": row.metrics.get("totalUsers", 0.0),
            "key_events": row.metrics.get("keyEvents", 0.0),
            "revenue": row.metrics.get("totalRevenue", 0.0),
        }
        for row in ga4_data.rows
    ]

    return correlate_campaigns(meta_rows, ga4_rows)
