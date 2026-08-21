import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function OverviewPage() {
  return (
    <>
      <PageHeader
        title="Overview"
        description="Today's spend, purchases, CPA, ROAS, and account-wide warnings."
      />
      <EmptyState
        title="Not connected yet"
        description="This page ships in Phase 2 once the Meta Ads read-only client is wired up. See docs/research/architecture-decision.md."
      />
    </>
  );
}
