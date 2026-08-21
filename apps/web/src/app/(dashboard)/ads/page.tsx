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
import type { MetaAd } from "@/lib/types";

export default function AdsPage() {
  const { data, isLoading, error } = useQuery<MetaAd[]>({
    queryKey: ["meta", "ads"],
    queryFn: () => api.get<MetaAd[]>("/api/meta/ads"),
    retry: false,
  });

  const notConnected = error instanceof ApiError && error.status === 503;

  return (
    <>
      <PageHeader
        title="Ads"
        description="Status per ad. Creative previews ship in Phase 4."
      />

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : notConnected ? (
        <EmptyState title="Meta not connected" description="Connect Meta Ads to see ads here." />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No ads" description="This ad account has no ads yet." />
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ad</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Ad set ID</TableHead>
                  <TableHead>Campaign ID</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="max-w-64 truncate font-medium">{a.name}</TableCell>
                    <TableCell>
                      <StatusBadge status={a.effective_status} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{a.adset_id ?? "—"}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {a.campaign_id ?? "—"}
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
