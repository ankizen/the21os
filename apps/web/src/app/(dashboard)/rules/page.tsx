"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { OperationalMode, SystemSettings } from "@/lib/types";

const MODE_DESCRIPTIONS: Record<OperationalMode, string> = {
  DRY_RUN: "Validates every write and shows what would happen — nothing is sent to Meta/GA4.",
  READ_ONLY: "Reads data only. Every write is rejected.",
  SUPERVISED: "Writes require human approval before executing.",
  AUTONOMOUS: "Claude can act within the ceilings below without per-action approval.",
};

const CENT_FIELDS: { key: keyof SystemSettings; label: string }[] = [
  { key: "max_daily_spend_cents", label: "Max daily spend" },
  { key: "max_campaign_budget_cents", label: "Max campaign budget" },
  { key: "require_approval_over_cents", label: "Require approval over" },
];

const COUNT_FIELDS: { key: keyof SystemSettings; label: string }[] = [
  { key: "max_budget_increase_pct", label: "Max budget increase (%)" },
  { key: "max_new_campaigns_per_day", label: "Max new campaigns / day" },
  { key: "max_ads_per_campaign", label: "Max ads per campaign" },
];

export default function RulesPage() {
  const { data, isLoading } = useQuery<SystemSettings>({
    queryKey: ["system", "settings"],
    queryFn: () => api.get<SystemSettings>("/api/system/settings"),
  });

  return (
    <>
      <PageHeader title="Rules" description="Operational mode and hard-coded safety ceilings." />
      {isLoading || !data ? <Skeleton className="h-64 w-full max-w-xl" /> : <RulesForm initial={data} />}
    </>
  );
}

function RulesForm({ initial }: { initial: SystemSettings }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SystemSettings>(initial);

  const save = useMutation({
    mutationFn: (body: SystemSettings) => api.put<SystemSettings>("/api/system/settings", body),
    onSuccess: (updated) => {
      queryClient.setQueryData(["system", "settings"], updated);
      setForm(updated);
      toast.success("Rules updated");
    },
    onError: () => toast.error("Could not save rules"),
  });

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle className="text-sm font-medium">Operational mode</CardTitle>
        <CardDescription>{MODE_DESCRIPTIONS[form.operational_mode]}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        <Select
          value={form.operational_mode}
          onValueChange={(value) => setForm({ ...form, operational_mode: value as OperationalMode })}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(MODE_DESCRIPTIONS) as OperationalMode[]).map((mode) => (
              <SelectItem key={mode} value={mode}>
                {mode.replace("_", " ")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {CENT_FIELDS.map(({ key, label }) => (
            <div key={key} className="flex flex-col gap-1.5">
              <Label htmlFor={key}>{label} (cents)</Label>
              <Input
                id={key}
                type="number"
                min={0}
                value={form[key] as number}
                onChange={(e) => setForm({ ...form, [key]: Number(e.target.value) })}
              />
              <p className="text-xs text-muted-foreground">₹{((form[key] as number) / 100).toFixed(2)}</p>
            </div>
          ))}
          {COUNT_FIELDS.map(({ key, label }) => (
            <div key={key} className="flex flex-col gap-1.5">
              <Label htmlFor={key}>{label}</Label>
              <Input
                id={key}
                type="number"
                min={0}
                value={form[key] as number}
                onChange={(e) => setForm({ ...form, [key]: Number(e.target.value) })}
              />
            </div>
          ))}
        </div>

        <Button className="self-start" onClick={() => save.mutate(form)} disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save rules"}
        </Button>
      </CardContent>
    </Card>
  );
}
