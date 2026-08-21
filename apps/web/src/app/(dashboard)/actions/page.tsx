"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
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
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { AuditLogEntry } from "@/lib/types";

export default function ActionsPage() {
  const { data, isLoading } = useQuery<AuditLogEntry[]>({
    queryKey: ["audit"],
    queryFn: () => api.get<AuditLogEntry[]>("/api/audit"),
    refetchInterval: 30_000,
  });

  return (
    <>
      <PageHeader title="Actions" description="Full audit trail of everything the system has done." />
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No actions yet" description="Every meaningful action — logins, rule changes, and later Meta/GA4 writes — will appear here." />
      ) : (
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
                  <TableCell className="font-mono text-xs">{entry.action}</TableCell>
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
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </>
  );
}
