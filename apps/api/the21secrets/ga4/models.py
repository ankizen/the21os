from pydantic import BaseModel


class PropertyInfo(BaseModel):
    name: str
    display_name: str
    time_zone: str
    currency_code: str


class ReportRow(BaseModel):
    dimensions: dict[str, str]
    metrics: dict[str, float]


class Report(BaseModel):
    rows: list[ReportRow]
    row_count: int
