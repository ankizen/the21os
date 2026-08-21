import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

export function StatCard({
  icon: Icon,
  label,
  value,
  caption,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  caption?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/25 to-[oklch(0.6_0.18_300/0.25)] text-primary">
          <Icon className="size-4.5" />
        </span>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="font-heading text-xl font-semibold tracking-tight">{value}</p>
          {caption && <p className="text-[11px] text-muted-foreground">{caption}</p>}
        </div>
      </CardContent>
    </Card>
  );
}
