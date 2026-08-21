from pydantic import BaseModel


class AccountInfo(BaseModel):
    id: str
    name: str | None = None
    currency: str
    timezone_name: str
    account_status: int
    amount_spent: str


class Campaign(BaseModel):
    id: str
    name: str
    status: str
    effective_status: str
    objective: str | None = None
    daily_budget: str | None = None
    lifetime_budget: str | None = None


class AdSet(BaseModel):
    id: str
    name: str
    status: str
    effective_status: str
    campaign_id: str | None = None
    optimization_goal: str | None = None
    daily_budget: str | None = None
    lifetime_budget: str | None = None


class Ad(BaseModel):
    id: str
    name: str
    status: str
    effective_status: str
    adset_id: str | None = None
    campaign_id: str | None = None
    creative_id: str | None = None


class Creative(BaseModel):
    id: str
    name: str
    status: str | None = None
    thumbnail_url: str | None = None
    image_url: str | None = None
    video_id: str | None = None
    object_type: str | None = None
    body: str | None = None
    title: str | None = None
    call_to_action_type: str | None = None
    usage_count: int = 0


class Insights(BaseModel):
    entity_id: str | None = None
    entity_name: str | None = None
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    reach: int | None = None
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    purchases: float = 0.0
    purchase_value: float = 0.0
    cpa: float | None = None
    roas: float | None = None
    date_start: str | None = None
    date_stop: str | None = None
