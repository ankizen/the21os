"use client";

import { useQuery } from "@tanstack/react-query";

import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/empty-state";
import { Ga4ReportTable } from "@/components/ga4-report-table";
import { PageHeader } from "@/components/page-header";
import { api, ApiError } from "@/lib/api";
import type { Ga4Report } from "@/lib/types";

const REPORTS = [
  { value: "landing-pages", label: "Landing pages" },
  { value: "campaigns", label: "Campaigns" },
  { value: "traffic-sources", label: "Traffic sources" },
  { value: "conversions", label: "Key events" },
  { value: "revenue", label: "Revenue" },
] as const;

function ReportTab({ endpoint }: { endpoint: string }) {
  const { data, isLoading } = useQuery<Ga4Report>({
    queryKey: ["ga4", "reports", endpoint],
    queryFn: () => api.get<Ga4Report>(`/api/ga4/reports/${endpoint}`),
    retry: false,
  });

  if (isLoading) return <Skeleton className="h-96 w-full" />;
  return <Ga4ReportTable report={data} />;
}

export default function AnalyticsPage() {
  const property = useQuery({
    queryKey: ["ga4", "property"],
    queryFn: () => api.get("/api/ga4/property"),
    retry: false,
  });

  const notConnected = property.error instanceof ApiError && property.error.status === 503;

  return (
    <>
      <PageHeader title="Analytics" description="GA4 traffic, conversions, and revenue — last 28 days." />

      {property.isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : notConnected ? (
        <EmptyState
          title="GA4 not connected"
          description="Set GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_PROJECT_ID / GA4_PROPERTY_ID to see analytics here."
        />
      ) : (
        <Tabs defaultValue="campaigns">
          <TabsList>
            {REPORTS.map((r) => (
              <TabsTrigger key={r.value} value={r.value}>
                {r.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {REPORTS.map((r) => (
            <TabsContent key={r.value} value={r.value}>
              <ReportTab endpoint={r.value} />
            </TabsContent>
          ))}
        </Tabs>
      )}
    </>
  );
}
