"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { api, ApiError } from "@/lib/api";
import type { CommandCenterStatus, Ga4PropertyInfo, MetaAccountInfo } from "@/lib/types";

export default function IntegrationsPage() {
  const meta = useQuery<MetaAccountInfo>({
    queryKey: ["meta", "account"],
    queryFn: () => api.get<MetaAccountInfo>("/api/meta/account"),
    retry: false,
  });
  const ga4 = useQuery<Ga4PropertyInfo>({
    queryKey: ["ga4", "property"],
    queryFn: () => api.get<Ga4PropertyInfo>("/api/ga4/property"),
    retry: false,
  });
  const claude = useQuery<CommandCenterStatus>({
    queryKey: ["command-center", "status"],
    queryFn: () => api.get<CommandCenterStatus>("/api/command-center/status"),
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
            {ga4.isLoading ? (
              <Skeleton className="h-5 w-20" />
            ) : ga4.isSuccess ? (
              <Badge className="bg-emerald-600 text-white">Connected</Badge>
            ) : (
              <Badge variant="outline" className="text-muted-foreground">
                Not connected
              </Badge>
            )}
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">GA4 Data API + Admin API</p>
            {ga4.data ? (
              <p className="mt-2 text-xs text-muted-foreground">
                {ga4.data.display_name} · {ga4.data.currency_code} · {ga4.data.name}
              </p>
            ) : (
              <p className="mt-2 text-xs text-muted-foreground">
                Set GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_PROJECT_ID / GA4_PROPERTY_ID.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Claude / MCP</CardTitle>
            {claude.isLoading ? (
              <Skeleton className="h-5 w-20" />
            ) : claude.data?.configured ? (
              <Badge className="bg-emerald-600 text-white">Connected</Badge>
            ) : (
              <Badge variant="outline" className="text-muted-foreground">
                Not connected
              </Badge>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">In-process tool access for the AI Command Center</p>
              <p className="mt-2 text-xs text-muted-foreground">
                {claude.data?.configured
                  ? `32 tools — reads + safety-gated writes${
                      claude.data.source === "database" ? ` · key ${claude.data.key_preview}` : " · via ANTHROPIC_API_KEY env"
                    }`
                  : "Set a key below, or ANTHROPIC_API_KEY in the environment."}
              </p>
            </div>
            <ClaudeKeyForm />
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function ClaudeKeyForm() {
  const queryClient = useQueryClient();
  const [apiKey, setApiKey] = useState("");

  const save = useMutation({
    mutationFn: (key: string) =>
      api.put<CommandCenterStatus>("/api/command-center/key", { api_key: key }),
    onSuccess: (status) => {
      queryClient.setQueryData(["command-center", "status"], status);
      setApiKey("");
      toast.success("Anthropic API key updated");
    },
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof err.body === "object" && err.body && "detail" in err.body
          ? String((err.body as { detail: unknown }).detail)
          : "Could not save the key";
      toast.error(detail);
    },
  });

  return (
    <div className="flex gap-2 border-t pt-3">
      <Input
        type="password"
        placeholder="sk-ant-…"
        value={apiKey}
        onChange={(e) => setApiKey(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && apiKey.trim() && !save.isPending) save.mutate(apiKey.trim());
        }}
      />
      <Button
        size="sm"
        disabled={save.isPending || !apiKey.trim()}
        onClick={() => save.mutate(apiKey.trim())}
      >
        {save.isPending ? "Saving…" : "Update key"}
      </Button>
    </div>
  );
}
