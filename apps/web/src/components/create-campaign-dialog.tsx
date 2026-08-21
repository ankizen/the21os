"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const OBJECTIVES = [
  "OUTCOME_SALES",
  "OUTCOME_LEADS",
  "OUTCOME_TRAFFIC",
  "OUTCOME_ENGAGEMENT",
  "OUTCOME_AWARENESS",
  "OUTCOME_APP_PROMOTION",
];

export function CreateCampaignDialog({
  onSubmit,
  isPending,
}: {
  onSubmit: (body: { name: string; objective: string; daily_budget_cents: number }) => void;
  isPending: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [objective, setObjective] = useState("OUTCOME_SALES");
  const [rupees, setRupees] = useState("");

  function submit() {
    const cents = Math.round(Number(rupees) * 100);
    if (!name.trim() || !Number.isFinite(cents) || cents <= 0) return;
    onSubmit({ name: name.trim(), objective, daily_budget_cents: cents });
    setOpen(false);
    setName("");
    setRupees("");
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button size="sm" className="gap-1.5">
            <Plus className="size-4" />
            Create campaign
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create campaign</DialogTitle>
          <DialogDescription>
            Always created PAUSED — goes through the safety pipeline like every other write.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="objective">Objective</Label>
            <Select value={objective} onValueChange={(v) => v && setObjective(v)}>
              <SelectTrigger id="objective" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {OBJECTIVES.map((o) => (
                  <SelectItem key={o} value={o}>
                    {o.replace("OUTCOME_", "").replace(/_/g, " ").toLowerCase()}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="budget">Daily budget (₹)</Label>
            <Input
              id="budget"
              type="number"
              min={1}
              step="0.01"
              value={rupees}
              onChange={(e) => setRupees(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={isPending}>
            {isPending ? "Creating…" : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
