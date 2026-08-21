"use client";

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

export function BudgetEditDialog({
  name,
  currentBudgetCents,
  onSubmit,
  isPending,
  trigger,
}: {
  name: string;
  currentBudgetCents: number;
  onSubmit: (dailyBudgetCents: number) => void;
  isPending: boolean;
  trigger: React.ReactElement;
}) {
  const [open, setOpen] = useState(false);
  const [rupees, setRupees] = useState((currentBudgetCents / 100).toString());

  function submit() {
    const cents = Math.round(Number(rupees) * 100);
    if (!Number.isFinite(cents) || cents <= 0) return;
    onSubmit(cents);
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={trigger} />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Update daily budget</DialogTitle>
          <DialogDescription>{name}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-2">
          <Label htmlFor="budget">Daily budget (₹)</Label>
          <Input
            id="budget"
            type="number"
            min={1}
            step="0.01"
            value={rupees}
            onChange={(e) => setRupees(e.target.value)}
            autoFocus
          />
          <p className="text-xs text-muted-foreground">
            Currently ₹{(currentBudgetCents / 100).toFixed(2)}/day. Goes through the safety pipeline like
            any other write — see Rules for the ceilings that apply.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={isPending}>
            {isPending ? "Saving…" : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
