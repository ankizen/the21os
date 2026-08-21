"use client";

import { useQuery } from "@tanstack/react-query";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { api, ApiError } from "@/lib/api";
import { formatMinorUnits } from "@/lib/format";
import type { MetaAdSet } from "@/lib/types";

export default function AdSetsPage() {
  const { data, isLoading, error } = useQuery<MetaAdSet[]>({
    queryKey: ["meta", "adsets"],
    queryFn: () => api.get<MetaAdSet[]>("/api/meta/adsets"),
    retry: false,
  });

  const notConnected = error instanceof ApiError && error.status === 503;

  return (
    <>
      <PageHeader title="Ad Sets" description="Targeting, budget, and status per ad set." />

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : notConnected ? (
        <EmptyState title="Meta not connected" description="Connect Meta Ads to see ad sets here." />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No ad sets" description="This ad account has no ad sets yet." />
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ad set</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Optimization goal</TableHead>
                  <TableHead className="text-right">Daily budget</TableHead>
                  <TableHead className="text-right">Lifetime budget</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="max-w-64 truncate font-medium">{a.name}</TableCell>
                    <TableCell>
                      <StatusBadge status={a.effective_status} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {a.optimization_goal ?? "—"}
                    </TableCell>
                    <TableCell className="text-right">{formatMinorUnits(a.daily_budget)}</TableCell>
                    <TableCell className="text-right">{formatMinorUnits(a.lifetime_budget)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </>
  );
}
