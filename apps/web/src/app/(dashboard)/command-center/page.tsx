import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function CommandCenterPage() {
  return (
    <>
      <PageHeader
        title="AI Command Center"
        description={'Ask Claude about your campaigns — e.g. "Which ads are wasting money?"'}
      />
      <EmptyState
        title="Not built yet"
        description="The Claude tool-use loop ships in Phase 6, once Meta/GA4 tools exist for it to call."
      />
    </>
  );
}
