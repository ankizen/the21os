"use client";

import { useQuery } from "@tanstack/react-query";
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
import { api } from "@/lib/api";
import type { MetaAdSet, MetaCreative } from "@/lib/types";

export function CreateAdDialog({
  onSubmit,
  isPending,
}: {
  onSubmit: (body: { name: string; adset_id: string; creative_id: string }) => void;
  isPending: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [adsetId, setAdsetId] = useState<string | null>(null);
  const [creativeId, setCreativeId] = useState<string | null>(null);

  const adsets = useQuery<MetaAdSet[]>({
    queryKey: ["meta", "adsets"],
    queryFn: () => api.get<MetaAdSet[]>("/api/meta/adsets"),
    enabled: open,
  });
  const creatives = useQuery<MetaCreative[]>({
    queryKey: ["meta", "creatives"],
    queryFn: () => api.get<MetaCreative[]>("/api/meta/creatives"),
    enabled: open,
  });

  function submit() {
    if (!name.trim() || !adsetId || !creativeId) return;
    onSubmit({ name: name.trim(), adset_id: adsetId, creative_id: creativeId });
    setOpen(false);
    setName("");
    setAdsetId(null);
    setCreativeId(null);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button size="sm" className="gap-1.5">
            <Plus className="size-4" />
            Create ad
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create ad</DialogTitle>
          <DialogDescription>
            Always created PAUSED — goes through the safety pipeline like every other write.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="ad-name">Name</Label>
            <Input id="ad-name" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="ad-adset">Ad set</Label>
            <Select value={adsetId ?? undefined} onValueChange={(v) => setAdsetId(v)}>
              <SelectTrigger id="ad-adset" className="w-full">
                <SelectValue placeholder={adsets.isLoading ? "Loading…" : "Choose an ad set"} />
              </SelectTrigger>
              <SelectContent>
                {(adsets.data ?? []).map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="ad-creative">Creative</Label>
            <Select value={creativeId ?? undefined} onValueChange={(v) => setCreativeId(v)}>
              <SelectTrigger id="ad-creative" className="w-full">
                <SelectValue placeholder={creatives.isLoading ? "Loading…" : "Choose a creative"} />
              </SelectTrigger>
              <SelectContent>
                {(creatives.data ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {creatives.data?.length === 0 && (
              <p className="text-xs text-muted-foreground">
                No creatives yet — create one on the Creatives page first.
              </p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={isPending || !name || !adsetId || !creativeId}>
            {isPending ? "Creating…" : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
