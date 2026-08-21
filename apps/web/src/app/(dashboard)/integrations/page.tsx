"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { api } from "@/lib/api";
import type { MetaAccountInfo } from "@/lib/types";

export default function IntegrationsPage() {
  const meta = useQuery<MetaAccountInfo>({
    queryKey: ["meta", "account"],
    queryFn: () => api.get<MetaAccountInfo>("/api/meta/account"),
    retry: false,
  });

  return (
    <>
      <PageHeader title="Integrations" description="Connection status for each external system." />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Meta Ads</CardTitle>
            {meta.isLoading ? (
              <Skeleton className="h-5 w-20" />
            ) : meta.isSuccess ? (
              <Badge className="bg-emerald-600 text-white">Connected</Badge>
            ) : (
              <Badge variant="outline" className="text-muted-foreground">
                Not connected
              </Badge>
            )}
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Marketing API {meta.data ? "" : "v26.0 "}via facebook-business SDK
            </p>
            {meta.data ? (
              <p className="mt-2 text-xs text-muted-foreground">
                {meta.data.name} · {meta.data.currency} · {meta.data.id}
              </p>
            ) : (
              <p className="mt-2 text-xs text-muted-foreground">
                Set META_APP_ID / META_APP_SECRET / META_ACCESS_TOKEN / META_DEFAULT_AD_ACCOUNT_ID.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Google Analytics 4</CardTitle>
            <Badge variant="outline" className="text-muted-foreground">
              Not connected
            </Badge>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">GA4 Data API + Admin API</p>
            <p className="mt-2 text-xs text-muted-foreground">Ships in Phase 5</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Claude / MCP</CardTitle>
            <Badge variant="outline" className="text-muted-foreground">
              Not connected
            </Badge>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Tool access for the AI Command Center</p>
            <p className="mt-2 text-xs text-muted-foreground">Ships in Phase 6</p>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
