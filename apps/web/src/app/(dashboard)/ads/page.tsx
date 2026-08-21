"use client";

import { useQuery } from "@tanstack/react-query";
import { Pause, Play } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CreateAdDialog } from "@/components/create-ad-dialog";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { api, ApiError } from "@/lib/api";
import type { MetaAd } from "@/lib/types";
import { useWriteAction } from "@/lib/writes";

const INVALIDATE = [["meta", "ads"]];

export default function AdsPage() {
  const { data, isLoading, error } = useQuery<MetaAd[]>({
    queryKey: ["meta", "ads"],
    queryFn: () => api.get<MetaAd[]>("/api/meta/ads"),
    retry: false,
  });

  const pause = useWriteAction((v) => `/api/meta/ads/${v.id}/pause`, { invalidate: INVALIDATE });
  const resume = useWriteAction((v) => `/api/meta/ads/${v.id}/resume`, { invalidate: INVALIDATE });
  const create = useWriteAction("/api/meta/ads", { invalidate: INVALIDATE });

  const notConnected = error instanceof ApiError && error.status === 503;

  return (
    <>
      <PageHeader title="Ads" description="Status per ad, and which creative each one uses.">
        {!notConnected && !isLoading && (
          <CreateAdDialog isPending={create.isPending} onSubmit={(body) => create.mutate(body)} />
        )}
      </PageHeader>

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
                  <TableHead>Creative ID</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((a) => {
                  const isActive = a.effective_status === "ACTIVE";
                  return (
                    <TableRow key={a.id}>
                      <TableCell className="max-w-64 truncate font-medium">{a.name}</TableCell>
                      <TableCell>
                        <StatusBadge status={a.effective_status} />
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{a.adset_id ?? "—"}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {a.campaign_id ?? "—"}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {a.creative_id ?? "—"}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7"
                            title={isActive ? "Pause" : "Resume"}
                            disabled={pause.isPending || resume.isPending}
                            onClick={() => (isActive ? pause : resume).mutate({ id: a.id })}
                          >
                            {isActive ? <Pause className="size-3.5" /> : <Play className="size-3.5" />}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </>
  );
}
