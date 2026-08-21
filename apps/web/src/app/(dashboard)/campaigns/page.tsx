import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function CampaignsPage() {
  return (
    <>
      <PageHeader title="Campaigns" description="Status, spend, CTR, CPC, purchases, CPA, ROAS." />
      <EmptyState
        title="Not connected yet"
        description="Campaign data ships in Phase 2 with the Meta Ads read-only client."
      />
    </>
  );
}
