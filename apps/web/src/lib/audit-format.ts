import type { AuditLogEntry } from "@/lib/types";

const ACTION_LABELS: Record<string, string> = {
  "auth.login": "Signed in",
  "auth.totp_enable": "Two-factor authentication enabled",
  "auth.totp_disable": "Two-factor authentication disabled",
  "settings.update": "Rules updated",
  "campaign.create": "Campaign created",
  "campaign.budget_update": "Campaign budget updated",
  "campaign.pause": "Campaign paused",
  "campaign.resume": "Campaign resumed",
  "campaign.duplicate": "Campaign duplicated",
  "adset.budget_update": "Ad set budget updated",
  "adset.pause": "Ad set paused",
  "adset.resume": "Ad set resumed",
  "ad.pause": "Ad paused",
  "ad.resume": "Ad resumed",
};

export function describeAuditEntry(entry: AuditLogEntry): string {
  return ACTION_LABELS[entry.action] ?? entry.action;
}

// Mirrors safety/rollback.py's _PAUSE_RESUME_INVERSE ∪ _BUDGET_ACTIONS —
// only these action types have a working rollback endpoint.
const REVERSIBLE_ACTIONS = new Set([
  "campaign.pause",
  "campaign.resume",
  "campaign.budget_update",
  "adset.pause",
  "adset.resume",
  "adset.budget_update",
  "ad.pause",
  "ad.resume",
]);

export function isRollbackable(entry: AuditLogEntry): boolean {
  return entry.success && REVERSIBLE_ACTIONS.has(entry.action);
}
