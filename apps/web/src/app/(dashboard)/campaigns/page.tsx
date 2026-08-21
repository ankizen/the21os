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
import { formatCurrency, formatNumber, formatPercent, formatRatio } from "@/lib/format";
import type { MetaCampaign, MetaInsights } from "@/lib/types";

export default function CampaignsPage() {
  const campaignsQuery = useQuery<MetaCampaign[]>({
    queryKey: ["meta", "campaigns"],
    queryFn: () => api.get<MetaCampaign[]>("/api/meta/campaigns"),
    retry: false,
  });
  const insightsQuery = useQuery<MetaInsights[]>({
    queryKey: ["meta", "insights", "campaigns", "last_30d"],
    queryFn: () => api.get<MetaInsights[]>("/api/meta/insights/campaigns?date_preset=last_30d"),
    retry: false,
    enabled: campaignsQuery.isSuccess,
  });

  const isLoading = campaignsQuery.isLoading;
  const notConnected =
    campaignsQuery.error instanceof ApiError && campaignsQuery.error.status === 503;

  const insightsByCampaign = new Map((insightsQuery.data ?? []).map((i) => [i.entity_id, i]));

  return (
    <>
      <PageHeader title="Campaigns" description="Status, spend, CTR, CPC, purchases, CPA, ROAS (last 30 days)." />

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : notConnected ? (
        <EmptyState
          title="Meta not connected"
          description="Set META_APP_ID / META_APP_SECRET / META_ACCESS_TOKEN / META_DEFAULT_AD_ACCOUNT_ID to see real campaigns here."
        />
      ) : !campaignsQuery.data || campaignsQuery.data.length === 0 ? (
        <EmptyState title="No campaigns" description="This ad account has no campaigns yet." />
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Campaign</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Objective</TableHead>
                  <TableHead className="text-right">Spend</TableHead>
                  <TableHead className="text-right">CTR</TableHead>
                  <TableHead className="text-right">CPC</TableHead>
                  <TableHead className="text-right">Purchases</TableHead>
                  <TableHead className="text-right">CPA</TableHead>
                  <TableHead className="text-right">ROAS</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaignsQuery.data.map((c) => {
                  const insight = insightsByCampaign.get(c.id);
                  return (
                    <TableRow key={c.id}>
                      <TableCell className="max-w-64 truncate font-medium">{c.name}</TableCell>
                      <TableCell>
                        <StatusBadge status={c.effective_status} />
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {c.objective ?? "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {insight ? formatCurrency(insight.spend) : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {insight ? formatPercent(insight.ctr) : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {insight && insight.cpc !== null ? formatCurrency(insight.cpc) : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {insight ? formatNumber(insight.purchases) : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {insight && insight.cpa !== null ? formatCurrency(insight.cpa) : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        {insight ? formatRatio(insight.roas) : "—"}
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
