from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

from the21os.ga4.client import call_ga4, get_data_client, property_path
from the21os.ga4.formatters import to_report
from the21os.ga4.models import Report


async def run_report(
    dimensions: list[str],
    metrics: list[str],
    start_date: str = "28daysAgo",
    end_date: str = "today",
    property_id: str | None = None,
    limit: int = 100,
) -> Report:
    client = get_data_client()
    request = RunReportRequest(
        property=property_path(property_id),
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=limit,
    )

    def fetch():
        return client.run_report(request)

    response = await call_ga4(fetch)
    return to_report(response)


async def landing_page_report(
    start_date: str = "28daysAgo", end_date: str = "today", property_id: str | None = None
) -> Report:
    return await run_report(
        dimensions=["landingPage", "sessionSourceMedium"],
        metrics=["sessions", "totalUsers", "keyEvents", "totalRevenue"],
        start_date=start_date,
        end_date=end_date,
        property_id=property_id,
    )


async def campaign_report(
    start_date: str = "28daysAgo", end_date: str = "today", property_id: str | None = None
) -> Report:
    return await run_report(
        dimensions=["sessionCampaignName", "sessionSourceMedium"],
        metrics=["sessions", "totalUsers", "keyEvents", "totalRevenue"],
        start_date=start_date,
        end_date=end_date,
        property_id=property_id,
    )


async def traffic_source_report(
    start_date: str = "28daysAgo", end_date: str = "today", property_id: str | None = None
) -> Report:
    return await run_report(
        dimensions=["sessionSourceMedium"],
        metrics=["sessions", "totalUsers", "newUsers"],
        start_date=start_date,
        end_date=end_date,
        property_id=property_id,
    )


async def conversion_report(
    start_date: str = "28daysAgo", end_date: str = "today", property_id: str | None = None
) -> Report:
    return await run_report(
        dimensions=["eventName"],
        metrics=["eventCount", "keyEvents"],
        start_date=start_date,
        end_date=end_date,
        property_id=property_id,
    )


async def revenue_report(
    start_date: str = "28daysAgo", end_date: str = "today", property_id: str | None = None
) -> Report:
    return await run_report(
        dimensions=["sessionSourceMedium"],
        metrics=["transactions", "totalRevenue", "purchaseRevenue"],
        start_date=start_date,
        end_date=end_date,
        property_id=property_id,
    )


async def compare_periods(
    dimensions: list[str],
    metrics: list[str],
    current_start: str,
    current_end: str,
    previous_start: str,
    previous_end: str,
    property_id: str | None = None,
) -> dict[str, Report]:
    current = await run_report(dimensions, metrics, current_start, current_end, property_id)
    previous = await run_report(dimensions, metrics, previous_start, previous_end, property_id)
    return {"current": current, "previous": previous}
