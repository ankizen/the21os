"use client";

import { useQuery } from "@tanstack/react-query";
import {
  DollarSign,
  Gauge,
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
import { api } from "@/lib/api";
import { relativeTime } from "@/lib/relative-time";
import type { AuditLogEntry } from "@/lib/types";

const QUICK_ACTIONS = [
  { href: "/rules", label: "Rules", icon: ShieldCheck },
  { href: "/actions", label: "Actions", icon: Zap },
  { href: "/system", label: "System", icon: Gauge },
  { href: "/command-center", label: "AI Command Center", icon: Sparkles },
];

export default function OverviewPage() {
  const { data: activity, isLoading } = useQuery<AuditLogEntry[]>({
    queryKey: ["audit", "recent"],
    queryFn: () => api.get<AuditLogEntry[]>("/api/audit?limit=5"),
  });

  return (
    <>
      <PageHeader
        title="Overview"
        description="Today's spend, purchases, CPA, ROAS, and account-wide warnings."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={DollarSign} label="Spend" value="—" caption="Not connected" />
        <StatCard icon={ShoppingCart} label="Purchases" value="—" caption="Not connected" />
        <StatCard icon={Target} label="CPA" value="—" caption="Not connected" />
        <StatCard icon={TrendingUp} label="ROAS" value="—" caption="Not connected" />
      </div>

      <Card className="mt-4 border-primary/25">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-medium">Connection Status</CardTitle>
          <Badge variant="secondary" className="rounded-full text-[10px]">
            Phase 2
          </Badge>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Plug className="size-5" />
          </span>
          <p className="text-sm font-medium">Not connected yet</p>
          <p className="max-w-sm text-sm text-muted-foreground">
            This page ships in Phase 2 once the Meta Ads read-only client is wired up.
          </p>
        </CardContent>
      </Card>

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
            {isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : !activity || activity.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No activity yet.</p>
            ) : (
              <ul className="space-y-3">
                {activity.map((entry) => (
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
