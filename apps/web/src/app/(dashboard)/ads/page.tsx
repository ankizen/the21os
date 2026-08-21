import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function AdsPage() {
  return (
    <>
      <PageHeader title="Ads" description="Creative preview, metrics, and status per ad." />
      <EmptyState
        title="Not connected yet"
        description="Ad data ships in Phase 2 with the Meta Ads read-only client."
      />
    </>
  );
}
