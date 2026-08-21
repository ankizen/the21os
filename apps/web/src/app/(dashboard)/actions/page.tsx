"use client";

import { useQuery } from "@tanstack/react-query";
import { Undo2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { describeAuditEntry, isRollbackable } from "@/lib/audit-format";
import { api } from "@/lib/api";
import type { ApprovalRequestEntry, AuditLogEntry } from "@/lib/types";
import { useWriteAction } from "@/lib/writes";

function ApprovalsTab() {
  const { data, isLoading } = useQuery<ApprovalRequestEntry[]>({
    queryKey: ["approvals", "pending"],
    queryFn: () => api.get<ApprovalRequestEntry[]>("/api/approvals?status=PENDING"),
    refetchInterval: 15_000,
  });
  const approve = useWriteAction((v) => `/api/approvals/${v.id}/approve`, {
    invalidate: [["approvals", "pending"], ["audit"]],
  });
  const reject = useWriteAction((v) => `/api/approvals/${v.id}/reject`, {
    invalidate: [["approvals", "pending"]],
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="Nothing pending"
        description="Writes that need sign-off (SUPERVISED mode, or AUTONOMOUS mode over your approval threshold) show up here."
      />
    );
  }

  return (
    <div className="space-y-3">
      {data.map((a) => (
        <div key={a.id} className="flex items-center justify-between rounded-lg border p-4">
          <div>
            <p className="text-sm font-medium">{a.summary}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Requested by {a.requested_by} · {new Date(a.created_at).toLocaleString()}
            </p>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={reject.isPending}
              onClick={() => reject.mutate({ id: a.id })}
            >
              Reject
            </Button>
            <Button size="sm" disabled={approve.isPending} onClick={() => approve.mutate({ id: a.id })}>
              Approve
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

function AuditLogTab() {
  const { data, isLoading } = useQuery<AuditLogEntry[]>({
    queryKey: ["audit"],
    queryFn: () => api.get<AuditLogEntry[]>("/api/audit"),
    refetchInterval: 30_000,
  });
  const rollback = useWriteAction((v) => `/api/audit/${v.id}/rollback`, {
    invalidate: [["audit"], ["meta", "campaigns"], ["meta", "adsets"], ["meta", "ads"]],
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No actions yet"
        description="Every meaningful action — logins, rule changes, and Meta writes — appears here."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Actor</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Entity</TableHead>
            <TableHead>Reason</TableHead>
            <TableHead className="text-right">Result</TableHead>
            <TableHead className="text-right">Undo</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((entry) => (
            <TableRow key={entry.id}>
              <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                {new Date(entry.created_at).toLocaleString()}
              </TableCell>
              <TableCell className="text-sm">{entry.actor}</TableCell>
              <TableCell className="text-sm text-muted-foreground">{entry.source}</TableCell>
              <TableCell className="text-sm">{describeAuditEntry(entry)}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {entry.entity ? `${entry.entity}${entry.entity_id ? ` #${entry.entity_id}` : ""}` : "—"}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {entry.decision_reason ?? "—"}
              </TableCell>
              <TableCell className="text-right">
                <Badge
                  variant={entry.success ? "default" : "destructive"}
                  className={entry.success ? "bg-emerald-600" : undefined}
                >
                  {entry.success ? "success" : "failed"}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                {isRollbackable(entry) && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-7"
                    title="Roll back"
                    disabled={rollback.isPending}
                    onClick={() => rollback.mutate({ id: entry.id })}
                  >
                    <Undo2 className="size-3.5" />
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export default function ActionsPage() {
  return (
    <>
      <PageHeader title="Actions" description="Approvals awaiting sign-off and the full audit trail." />
      <Tabs defaultValue="approvals">
        <TabsList>
          <TabsTrigger value="approvals">Approvals</TabsTrigger>
          <TabsTrigger value="log">Audit log</TabsTrigger>
        </TabsList>
        <TabsContent value="approvals">
          <ApprovalsTab />
        </TabsContent>
        <TabsContent value="log">
          <AuditLogTab />
        </TabsContent>
      </Tabs>
    </>
  );
}
