import { Badge } from "@/components/ui/badge";

const STATUS_STYLES: Record<string, string> = {
  ACTIVE: "bg-emerald-600 text-white",
  PAUSED: "bg-secondary text-secondary-foreground",
  ARCHIVED: "bg-muted text-muted-foreground",
  DELETED: "bg-destructive text-destructive-foreground",
  IN_PROCESS: "bg-amber-600 text-white",
  WITH_ISSUES: "bg-destructive text-destructive-foreground",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge className={STATUS_STYLES[status] ?? "bg-secondary text-secondary-foreground"}>
      {status.replace(/_/g, " ").toLowerCase()}
    </Badge>
  );
}
