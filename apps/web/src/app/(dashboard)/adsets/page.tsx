"use client";

import { useQuery } from "@tanstack/react-query";
import { Pause, PencilLine, Play } from "lucide-react";

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
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { api, ApiError } from "@/lib/api";
import { formatMinorUnits } from "@/lib/format";
import type { MetaAdSet } from "@/lib/types";
import { useWriteAction } from "@/lib/writes";

const INVALIDATE = [["meta", "adsets"]];

export default function AdSetsPage() {
  const { data, isLoading, error } = useQuery<MetaAdSet[]>({
    queryKey: ["meta", "adsets"],
    queryFn: () => api.get<MetaAdSet[]>("/api/meta/adsets"),
    retry: false,
  });

  const pause = useWriteAction((v) => `/api/meta/adsets/${v.id}/pause`, { invalidate: INVALIDATE });
  const resume = useWriteAction((v) => `/api/meta/adsets/${v.id}/resume`, { invalidate: INVALIDATE });
  const updateBudget = useWriteAction((v) => `/api/meta/adsets/${v.id}/budget`, {
    method: "PATCH",
    invalidate: INVALIDATE,
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
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((a) => {
                  const isActive = a.effective_status === "ACTIVE";
                  const budgetCents = a.daily_budget ? Number(a.daily_budget) : 0;
                  return (
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
                      <TableCell>
                        <div className="flex justify-end gap-1">
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
                          {a.daily_budget && (
                            <BudgetEditDialog
                              name={a.name}
                              currentBudgetCents={budgetCents}
                              isPending={updateBudget.isPending}
                              onSubmit={(daily_budget_cents) =>
                                updateBudget.mutate({ id: a.id, daily_budget_cents })
                              }
                              trigger={
                                <Button variant="ghost" size="icon" className="size-7" title="Edit budget">
                                  <PencilLine className="size-3.5" />
                                </Button>
                              }
                            />
                          )}
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
