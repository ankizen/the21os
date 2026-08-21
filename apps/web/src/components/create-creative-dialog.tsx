"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ImagePlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

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
import { api, ApiError } from "@/lib/api";
import type { WriteResponse } from "@/lib/writes";

const CTA_TYPES = ["LEARN_MORE", "SHOP_NOW", "SIGN_UP", "DOWNLOAD", "CONTACT_US", "SUBSCRIBE"];

export function CreateCreativeDialog() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [link, setLink] = useState("");
  const [headline, setHeadline] = useState("");
  const [cta, setCta] = useState("LEARN_MORE");

  const submit = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Pick an image first");
      const form = new FormData();
      form.append("file", file);
      const uploadResult = await api.postForm<WriteResponse>("/api/meta/assets/image", form);

      if (uploadResult.status !== "executed") {
        return { step: "upload" as const, response: uploadResult };
      }
      const imageHash = (uploadResult.result as { hash?: string } | null)?.hash;
      if (!imageHash) throw new Error("Upload succeeded but returned no image hash");

      const creativeResult = await api.post<WriteResponse>("/api/meta/creatives", {
        name: name || file.name,
        message,
        link,
        headline,
        call_to_action: cta,
        image_hash: imageHash,
      });
      return { step: "creative" as const, response: creativeResult };
    },
    onSuccess: ({ step, response }) => {
      if (step === "upload") {
        // dry_run/pending_approval/rejected on the upload itself — nothing
        // to chain into a creative yet.
        if (response.status === "dry_run") {
          toast.info("DRY_RUN — image upload validated, not sent to Meta", {
            description: "Switch modes in Rules to actually upload and create the creative.",
          });
        } else if (response.status === "rejected") {
          toast.error("Upload rejected", { description: response.reason ?? undefined });
        }
        return;
      }
      if (response.status === "executed") {
        toast.success("Creative created");
        queryClient.invalidateQueries({ queryKey: ["meta", "creatives"] });
        setOpen(false);
        setFile(null);
        setName("");
        setMessage("");
        setLink("");
        setHeadline("");
      } else if (response.status === "pending_approval") {
        toast.info("Image uploaded — creative queued for approval", {
          description: "Review it on the Actions page.",
        });
      } else if (response.status === "rejected") {
        toast.error("Creative rejected", { description: response.reason ?? undefined });
      }
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        const detail =
          typeof err.body === "object" && err.body && "detail" in err.body
            ? String((err.body as { detail: unknown }).detail)
            : "Request failed";
        toast.error(detail);
      } else {
        toast.error(err instanceof Error ? err.message : "Could not reach the server");
      }
    },
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button size="sm" className="gap-1.5">
            <ImagePlus className="size-4" />
            New creative
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New creative</DialogTitle>
          <DialogDescription>
            Uploads the image, then creates the creative from it — both go through the safety pipeline.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="file">Image</Label>
            <Input
              id="file"
              type="file"
              accept="image/*"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="creative-name">Name</Label>
            <Input
              id="creative-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={file?.name}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="headline">Headline</Label>
            <Input id="headline" value={headline} onChange={(e) => setHeadline(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="message">Primary text</Label>
            <Input id="message" value={message} onChange={(e) => setMessage(e.target.value)} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="link">Link</Label>
            <Input
              id="link"
              type="url"
              value={link}
              onChange={(e) => setLink(e.target.value)}
              placeholder="https://…"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="cta">Call to action</Label>
            <Select value={cta} onValueChange={(v) => v && setCta(v)}>
              <SelectTrigger id="cta" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CTA_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t.replace(/_/g, " ").toLowerCase()}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => submit.mutate()}
            disabled={submit.isPending || !file || !link || !headline}
          >
            {submit.isPending ? "Uploading…" : "Upload & create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
