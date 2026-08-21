import type { AuditLogEntry } from "@/lib/types";

const ACTION_LABELS: Record<string, string> = {
  "auth.login": "Signed in",
  "auth.totp_enable": "Two-factor authentication enabled",
  "auth.totp_disable": "Two-factor authentication disabled",
  "settings.update": "Rules updated",
};

export function describeAuditEntry(entry: AuditLogEntry): string {
  return ACTION_LABELS[entry.action] ?? entry.action;
}
