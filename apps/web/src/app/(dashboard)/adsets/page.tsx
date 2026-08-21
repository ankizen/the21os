import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function AdSetsPage() {
  return (
    <>
      <PageHeader title="Ad Sets" description="Performance table and targeting summary." />
      <EmptyState
        title="Not connected yet"
        description="Ad set data ships in Phase 2 with the Meta Ads read-only client."
      />
    </>
  );
}
