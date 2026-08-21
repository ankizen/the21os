import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function AnalyticsPage() {
  return (
    <>
      <PageHeader title="Analytics" description="GA4 traffic, conversions, and revenue." />
      <EmptyState
        title="Not connected yet"
        description="Google Analytics reporting ships in Phase 5."
      />
    </>
  );
}
