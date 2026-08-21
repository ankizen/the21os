"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  DollarSign,
  Megaphone,
  Plug,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { describeAuditEntry } from "@/lib/audit-format";
import { api, ApiError } from "@/lib/api";
import { formatCurrency, formatNumber, formatRatio } from "@/lib/format";
import { relativeTime } from "@/lib/relative-time";
import type { AuditLogEntry, MetaAccountInfo, MetaInsights } from "@/lib/types";

const QUICK_ACTIONS = [
  { href: "/campaigns", label: "Campaigns", icon: Megaphone },
  { href: "/rules", label: "Rules", icon: ShieldCheck },
  { href: "/actions", label: "Actions", icon: Zap },
  { href: "/command-center", label: "AI Command Center", icon: Sparkles },
];

export default function OverviewPage() {
  const account = useQuery<MetaAccountInfo>({
    queryKey: ["meta", "account"],
    queryFn: () => api.get<MetaAccountInfo>("/api/meta/account"),
    retry: false,
  });
  const insights = useQuery<MetaInsights>({
    queryKey: ["meta", "insights", "account", "today"],
    queryFn: () => api.get<MetaInsights>("/api/meta/insights/account?date_preset=today"),
    retry: false,
    enabled: account.isSuccess,
  });
  const activity = useQuery<AuditLogEntry[]>({
    queryKey: ["audit", "recent"],
    queryFn: () => api.get<AuditLogEntry[]>("/api/audit?limit=5"),
  });

  const notConnected = account.error instanceof ApiError && account.error.status === 503;
  const connected = account.isSuccess;

  return (
    <>
      <PageHeader
        title="Overview"
        description="Today's spend, purchases, CPA, ROAS, and account-wide warnings."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          icon={DollarSign}
          label="Spend"
          value={insights.data ? formatCurrency(insights.data.spend) : "—"}
          caption={connected ? "Today" : "Not connected"}
        />
        <StatCard
          icon={ShoppingCart}
          label="Purchases"
          value={insights.data ? formatNumber(insights.data.purchases) : "—"}
          caption={connected ? "Today" : "Not connected"}
        />
        <StatCard
          icon={Target}
          label="CPA"
          value={insights.data?.cpa != null ? formatCurrency(insights.data.cpa) : "—"}
          caption={connected ? "Today" : "Not connected"}
        />
        <StatCard
          icon={TrendingUp}
          label="ROAS"
          value={insights.data?.roas != null ? formatRatio(insights.data.roas) : "—"}
          caption={connected ? "Today" : "Not connected"}
        />
      </div>

      {connected ? (
        <Card className="mt-4 border-emerald-600/25">
          <CardContent className="flex items-center gap-3 py-4">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-600/15 text-emerald-500">
              <CheckCircle2 className="size-4" />
            </span>
            <div className="text-sm">
              <span className="font-medium">Connected</span>{" "}
              <span className="text-muted-foreground">
                — {account.data?.name ?? "Meta Ads account"} ({account.data?.currency})
              </span>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="mt-4 border-primary/25">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Connection Status</CardTitle>
            <Badge variant="secondary" className="rounded-full text-[10px]">
              {notConnected ? "Not configured" : "Loading"}
            </Badge>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Plug className="size-5" />
            </span>
            <p className="text-sm font-medium">Not connected yet</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Set META_APP_ID / META_APP_SECRET / META_ACCESS_TOKEN / META_DEFAULT_AD_ACCOUNT_ID to
              connect your ad account.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {QUICK_ACTIONS.map((action) => (
                <Link
                  key={action.href}
                  href={action.href}
                  className="flex flex-col items-center gap-2 rounded-lg border border-border py-4 text-center text-xs transition-colors hover:border-primary/40 hover:bg-accent"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <action.icon className="size-4" />
                  </span>
                  {action.label}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
            <Link href="/actions" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {activity.isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : !activity.data || activity.data.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No activity yet.</p>
            ) : (
              <ul className="space-y-3">
                {activity.data.map((entry) => (
                  <li key={entry.id} className="flex items-start gap-2.5 text-sm">
                    <span
                      className={`mt-1.5 size-1.5 shrink-0 rounded-full ${entry.success ? "bg-emerald-500" : "bg-destructive"}`}
                    />
                    <span className="min-w-0 flex-1">{describeAuditEntry(entry)}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {relativeTime(entry.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
