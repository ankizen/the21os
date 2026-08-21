"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/page-header";
import { api, ApiError } from "@/lib/api";
import type { CommandCenterStatus, Ga4PropertyInfo, MetaAccountInfo, WordPressStatus } from "@/lib/types";

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

      <div className="mt-4">
        <WordPressCard />
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

const EMPTY_WORDPRESS_FORM = {
  site_url: "",
  app_username: "",
  app_password: "",
  woo_consumer_key: "",
  woo_consumer_secret: "",
};

function WordPressCard() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(EMPTY_WORDPRESS_FORM);

  const status = useQuery<WordPressStatus>({
    queryKey: ["wordpress", "status"],
    queryFn: () => api.get<WordPressStatus>("/api/integrations/wordpress/status"),
    retry: false,
  });

  const save = useMutation({
    mutationFn: () => api.put<WordPressStatus>("/api/integrations/wordpress", form),
    onSuccess: (data) => {
      queryClient.setQueryData(["wordpress", "status"], data);
      setForm(EMPTY_WORDPRESS_FORM);
      toast.success(
        data.wp_connected && data.woo_connected
          ? "WordPress + WooCommerce connected"
          : "Saved — see connection status below",
      );
    },
    onError: (err) => {
      const detail =
        err instanceof ApiError && typeof err.body === "object" && err.body && "detail" in err.body
          ? String((err.body as { detail: unknown }).detail)
          : "Could not save the connection";
      toast.error(detail);
    },
  });

  const allFilled = Object.values(form).every((v) => v.trim().length > 0);
  const data = status.data;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">WordPress / WooCommerce</CardTitle>
        {status.isLoading ? (
          <Skeleton className="h-5 w-24" />
        ) : data?.configured ? (
          <div className="flex gap-1.5">
            <Badge
              className={data.wp_connected ? "bg-emerald-600 text-white" : undefined}
              variant={data.wp_connected ? undefined : "outline"}
            >
              WP {data.wp_connected ? "ok" : "error"}
            </Badge>
            <Badge
              className={data.woo_connected ? "bg-emerald-600 text-white" : undefined}
              variant={data.woo_connected ? undefined : "outline"}
            >
              Woo {data.woo_connected ? "ok" : "error"}
            </Badge>
          </div>
        ) : (
          <Badge variant="outline" className="text-muted-foreground">
            Not connected
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Read access for order data (ground truth alongside Meta/GA4) and, later, product + sales-page
          management — every write will go through the same safety pipeline as Meta writes.
        </p>

        {data?.configured && (
          <div className="space-y-0.5 text-xs">
            {data.wp_connected && <p className="text-muted-foreground">WordPress: signed in as {data.wp_user}</p>}
            {data.wp_error && <p className="text-destructive">WordPress: {data.wp_error}</p>}
            {data.woo_connected && (
              <p className="text-muted-foreground">WooCommerce: {data.woo_order_count} orders visible</p>
            )}
            {data.woo_error && <p className="text-destructive">WooCommerce: {data.woo_error}</p>}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <Label htmlFor="wp-site-url">Site URL</Label>
            <Input
              id="wp-site-url"
              placeholder="https://the21secrets.com"
              value={form.site_url}
              onChange={(e) => setForm({ ...form, site_url: e.target.value })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="wp-username">WordPress username</Label>
            <Input
              id="wp-username"
              value={form.app_username}
              onChange={(e) => setForm({ ...form, app_username: e.target.value })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="wp-app-password">Application Password</Label>
            <Input
              id="wp-app-password"
              type="password"
              placeholder="xxxx xxxx xxxx xxxx"
              value={form.app_password}
              onChange={(e) => setForm({ ...form, app_password: e.target.value })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="woo-key">WooCommerce Consumer Key</Label>
            <Input
              id="woo-key"
              type="password"
              placeholder="ck_…"
              value={form.woo_consumer_key}
              onChange={(e) => setForm({ ...form, woo_consumer_key: e.target.value })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="woo-secret">WooCommerce Consumer Secret</Label>
            <Input
              id="woo-secret"
              type="password"
              placeholder="cs_…"
              value={form.woo_consumer_secret}
              onChange={(e) => setForm({ ...form, woo_consumer_secret: e.target.value })}
            />
          </div>
        </div>

        <Button size="sm" disabled={!allFilled || save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? "Connecting…" : "Connect"}
        </Button>
      </CardContent>
    </Card>
  );
}
