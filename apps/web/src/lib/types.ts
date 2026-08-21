export type OperationalMode = "DRY_RUN" | "READ_ONLY" | "SUPERVISED" | "AUTONOMOUS";

export interface User {
  id: string;
  email: string;
  totp_enabled: boolean;
}

export interface LoginResponse {
  totp_required: boolean;
  user: User | null;
}

export interface SystemSettings {
  operational_mode: OperationalMode;
  max_daily_spend_cents: number;
  max_campaign_budget_cents: number;
  max_budget_increase_pct: number;
  max_new_campaigns_per_day: number;
  max_ads_per_campaign: number;
  require_approval_over_cents: number;
}

export interface AuditLogEntry {
  id: string;
  created_at: string;
  request_id: string;
  actor: string;
  source: string;
  action: string;
  entity: string | null;
  entity_id: string | null;
  params_json: Record<string, unknown> | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  decision_reason: string | null;
  success: boolean;
}

export interface SystemHealth {
  status: "ok" | "degraded";
  database: "ok" | "unreachable";
}

export interface MetaAccountInfo {
  id: string;
  name: string | null;
  currency: string;
  timezone_name: string;
  account_status: number;
  amount_spent: string;
}

export interface MetaCampaign {
  id: string;
  name: string;
  status: string;
  effective_status: string;
  objective: string | null;
  daily_budget: string | null;
  lifetime_budget: string | null;
}

export interface MetaAdSet {
  id: string;
  name: string;
  status: string;
  effective_status: string;
  campaign_id: string | null;
  optimization_goal: string | null;
  daily_budget: string | null;
  lifetime_budget: string | null;
}

export interface MetaAd {
  id: string;
  name: string;
  status: string;
  effective_status: string;
  adset_id: string | null;
  campaign_id: string | null;
  creative_id: string | null;
}

export interface MetaCreative {
  id: string;
  name: string;
  status: string | null;
  thumbnail_url: string | null;
  image_url: string | null;
  video_id: string | null;
  object_type: string | null;
  body: string | null;
  title: string | null;
  call_to_action_type: string | null;
  usage_count: number;
}

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";

export interface ApprovalRequestEntry {
  id: string;
  created_at: string;
  action: string;
  entity: string | null;
  entity_id: string | null;
  summary: string;
  status: ApprovalStatus;
  requested_by: string;
  decided_at: string | null;
  decided_by: string | null;
}

export interface MetaInsights {
  entity_id: string | null;
  entity_name: string | null;
  impressions: number;
  clicks: number;
  spend: number;
  reach: number | null;
  ctr: number | null;
  cpc: number | null;
  cpm: number | null;
  purchases: number;
  purchase_value: number;
  cpa: number | null;
  roas: number | null;
  date_start: string | null;
  date_stop: string | null;
}

export interface Ga4PropertyInfo {
  name: string;
  display_name: string;
  time_zone: string;
  currency_code: string;
}

export interface Ga4ReportRow {
  dimensions: Record<string, string>;
  metrics: Record<string, number>;
}

export interface Ga4Report {
  rows: Ga4ReportRow[];
  row_count: number;
}

export interface CommandCenterMessage {
  role: string;
  content: unknown;
}

export interface CommandCenterTrace {
  tool: string;
  input: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface CommandCenterAskResponse {
  reply: string;
  trace: CommandCenterTrace[];
  messages: CommandCenterMessage[];
}

export interface CommandCenterStatus {
  configured: boolean;
  source: "database" | "environment" | null;
  key_preview: string | null;
}

export interface CorrelationRow {
  campaign_id: string;
  campaign_name: string;
  meta_spend: number;
  meta_purchases: number;
  meta_purchase_value: number;
  ga4_sessions: number;
  ga4_users: number;
  ga4_key_events: number;
  ga4_revenue: number;
  has_ga4_data: boolean;
  conversion_discrepancy: number | null;
}
