"use client";

import { useQuery } from "@tanstack/react-query";
import { ImageOff, VideoIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateCreativeDialog } from "@/components/create-creative-dialog";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { api, ApiError } from "@/lib/api";
import type { MetaCreative } from "@/lib/types";

export default function CreativesPage() {
  const { data, isLoading, error } = useQuery<MetaCreative[]>({
    queryKey: ["meta", "creatives"],
    queryFn: () => api.get<MetaCreative[]>("/api/meta/creatives"),
    retry: false,
  });

  const notConnected = error instanceof ApiError && error.status === 503;

  return (
    <>
      <PageHeader
        title="Creatives"
        description="Creative library — thumbnails, usage, and status. Performance and fatigue detection ship in Phase 7 (optimization)."
      >
        {!notConnected && !isLoading && <CreateCreativeDialog />}
      </PageHeader>

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : notConnected ? (
        <EmptyState
          title="Meta not connected"
          description="Set META_APP_ID / META_APP_SECRET / META_ACCESS_TOKEN / META_DEFAULT_AD_ACCOUNT_ID to see creatives here."
        />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No creatives" description="Upload an image to create your first creative." />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {data.map((c) => (
            <Card key={c.id} className="overflow-hidden py-0">
              <div className="flex aspect-square items-center justify-center bg-muted">
                {c.thumbnail_url || c.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element -- external Meta CDN thumbnails, not worth next/image's remote-pattern config for a small internal tool
                  <img
                    src={c.thumbnail_url ?? c.image_url ?? undefined}
                    alt={c.name}
                    className="h-full w-full object-cover"
                  />
                ) : c.video_id ? (
                  <VideoIcon className="size-8 text-muted-foreground" />
                ) : (
                  <ImageOff className="size-8 text-muted-foreground" />
                )}
              </div>
              <CardContent className="space-y-1.5 p-3">
                <p className="truncate text-sm font-medium" title={c.name}>
                  {c.name}
                </p>
                <div className="flex items-center justify-between">
                  <Badge variant="secondary" className="text-[10px]">
                    {c.video_id ? "video" : "image"}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {c.usage_count} {c.usage_count === 1 ? "ad" : "ads"}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
