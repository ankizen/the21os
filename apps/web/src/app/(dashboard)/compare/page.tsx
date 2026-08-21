"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
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
import { api, ApiError } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";
import type { CorrelationRow } from "@/lib/types";

export default function ComparePage() {
  const { data, isLoading, error } = useQuery<CorrelationRow[]>({
    queryKey: ["analytics", "correlation"],
    queryFn: () => api.get<CorrelationRow[]>("/api/analytics/correlation"),
    retry: false,
  });

  const notConnected = error instanceof ApiError && error.status === 503;

  return (
    <>
      <PageHeader
        title="Compare"
        description="Meta-reported vs GA4-reported performance, joined by campaign — never blended into one number."
      />

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : notConnected ? (
        <EmptyState
          title="Not connected"
          description={
            error instanceof ApiError && typeof error.body === "object" && error.body && "detail" in error.body
              ? String((error.body as { detail: unknown }).detail)
              : "Connect both Meta and GA4 to compare."
          }
        />
      ) : !data || data.length === 0 ? (
        <EmptyState title="Nothing to compare" description="No campaigns with spend in this period." />
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Campaign</TableHead>
                  <TableHead className="text-right">Meta spend</TableHead>
                  <TableHead className="text-right">Meta purchases</TableHead>
                  <TableHead className="text-right">GA4 sessions</TableHead>
                  <TableHead className="text-right">GA4 key events</TableHead>
                  <TableHead className="text-right">Discrepancy</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((r) => (
                  <TableRow key={r.campaign_id}>
                    <TableCell className="max-w-64 truncate font-medium">{r.campaign_name}</TableCell>
                    <TableCell className="text-right">{formatCurrency(r.meta_spend)}</TableCell>
                    <TableCell className="text-right">{formatNumber(r.meta_purchases)}</TableCell>
                    <TableCell className="text-right">
                      {r.has_ga4_data ? formatNumber(r.ga4_sessions) : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      {r.has_ga4_data ? formatNumber(r.ga4_key_events) : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      {!r.has_ga4_data ? (
                        <Badge variant="outline" className="text-muted-foreground">
                          no GA4 data
                        </Badge>
                      ) : r.conversion_discrepancy !== null && Math.abs(r.conversion_discrepancy) >= 1 ? (
                        <span className="inline-flex items-center gap-1 text-amber-500">
                          <AlertTriangle className="size-3.5" />
                          {r.conversion_discrepancy > 0 ? "+" : ""}
                          {formatNumber(r.conversion_discrepancy)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </TableCell>
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
