from the21os.ga4.models import Report, ReportRow


def to_report(response) -> Report:
    """Flattens a GAPIC RunReportResponse/RunRealtimeReportResponse (both
    share the same dimension_headers/metric_headers/rows shape) into our
    Report model."""
    dim_names = [h.name for h in response.dimension_headers]
    metric_names = [h.name for h in response.metric_headers]
    rows = [
        ReportRow(
            dimensions=dict(zip(dim_names, [v.value for v in row.dimension_values], strict=True)),
            metrics=dict(zip(metric_names, [float(v.value) for v in row.metric_values], strict=True)),
        )
        for row in response.rows
    ]
    return Report(rows=rows, row_count=response.row_count)
