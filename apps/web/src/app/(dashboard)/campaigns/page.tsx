"use client";

import { useQuery } from "@tanstack/react-query";
import { Copy, Pause, PencilLine, Play } from "lucide-react";

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
import { BudgetEditDialog } from "@/components/budget-edit-dialog";
import { CreateCampaignDialog } from "@/components/create-campaign-dialog";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { api, ApiError } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent, formatRatio } from "@/lib/format";
import type { MetaCampaign, MetaInsights } from "@/lib/types";
import { useWriteAction } from "@/lib/writes";

const INVALIDATE = [["meta", "campaigns"], ["meta", "insights", "campaigns", "last_30d"]];

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

  const create = useWriteAction("/api/meta/campaigns", { invalidate: INVALIDATE });
  const pause = useWriteAction((v) => `/api/meta/campaigns/${v.id}/pause`, { invalidate: INVALIDATE });
  const resume = useWriteAction((v) => `/api/meta/campaigns/${v.id}/resume`, { invalidate: INVALIDATE });
  const duplicate = useWriteAction((v) => `/api/meta/campaigns/${v.id}/duplicate`, {
    invalidate: INVALIDATE,
  });
  const updateBudget = useWriteAction((v) => `/api/meta/campaigns/${v.id}/budget`, {
    method: "PATCH",
    invalidate: INVALIDATE,
  });

  const isLoading = campaignsQuery.isLoading;
  const notConnected = campaignsQuery.error instanceof ApiError && campaignsQuery.error.status === 503;

  const insightsByCampaign = new Map((insightsQuery.data ?? []).map((i) => [i.entity_id, i]));

  return (
    <>
      <PageHeader
        title="Campaigns"
        description="Status, spend, CTR, CPC, purchases, CPA, ROAS (last 30 days)."
      >
        {!notConnected && !isLoading && (
          <CreateCampaignDialog
            isPending={create.isPending}
            onSubmit={(body) => create.mutate(body)}
          />
        )}
      </PageHeader>

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
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaignsQuery.data.map((c) => {
                  const insight = insightsByCampaign.get(c.id);
                  const isActive = c.effective_status === "ACTIVE";
                  const budgetCents = c.daily_budget ? Number(c.daily_budget) : 0;
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
                      <TableCell>
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7"
                            title={isActive ? "Pause" : "Resume"}
                            disabled={pause.isPending || resume.isPending}
                            onClick={() =>
                              (isActive ? pause : resume).mutate({ id: c.id })
                            }
                          >
                            {isActive ? <Pause className="size-3.5" /> : <Play className="size-3.5" />}
                          </Button>
                          <BudgetEditDialog
                            name={c.name}
                            currentBudgetCents={budgetCents}
                            isPending={updateBudget.isPending}
                            onSubmit={(daily_budget_cents) =>
                              updateBudget.mutate({ id: c.id, daily_budget_cents })
                            }
                            trigger={
                              <Button variant="ghost" size="icon" className="size-7" title="Edit budget">
                                <PencilLine className="size-3.5" />
                              </Button>
                            }
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7"
                            title="Duplicate"
                            disabled={duplicate.isPending}
                            onClick={() => duplicate.mutate({ id: c.id })}
                          >
                            <Copy className="size-3.5" />
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
