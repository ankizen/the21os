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
