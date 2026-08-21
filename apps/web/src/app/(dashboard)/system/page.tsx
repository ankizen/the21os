"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { SystemHealth } from "@/lib/types";

function StatusBadge({ ok }: { ok: boolean }) {
  return (
    <Badge variant={ok ? "default" : "destructive"} className={ok ? "bg-emerald-600" : undefined}>
      {ok ? "ok" : "degraded"}
    </Badge>
  );
}

export default function SystemPage() {
  const { data, isLoading } = useQuery<SystemHealth>({
    queryKey: ["system", "health"],
    queryFn: () => api.get<SystemHealth>("/api/system/health"),
    refetchInterval: 30_000,
  });

  return (
    <>
      <PageHeader title="System" description="API and database health." />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API</CardTitle>
            {isLoading ? <Skeleton className="h-5 w-14" /> : <StatusBadge ok={data?.status === "ok"} />}
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">FastAPI backend, reachable from this dashboard.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            {isLoading ? (
              <Skeleton className="h-5 w-14" />
            ) : (
              <StatusBadge ok={data?.database === "ok"} />
            )}
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">PostgreSQL — app state and audit log.</p>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
