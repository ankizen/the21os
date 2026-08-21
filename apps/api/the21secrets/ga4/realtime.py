from google.analytics.data_v1beta.types import Dimension, Metric, RunRealtimeReportRequest

from the21secrets.ga4.client import call_ga4, get_data_client, property_path
from the21secrets.ga4.formatters import to_report
from the21secrets.ga4.models import Report


async def realtime_report(property_id: str | None = None) -> Report:
    client = get_data_client()
    request = RunRealtimeReportRequest(
        property=property_path(property_id),
        dimensions=[Dimension(name="unifiedScreenName"), Dimension(name="deviceCategory")],
        metrics=[Metric(name="activeUsers")],
    )

    def fetch():
        return client.run_realtime_report(request)

    response = await call_ga4(fetch)
    return to_report(response)
