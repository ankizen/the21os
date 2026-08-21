import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function ComparePage() {
  return (
    <>
      <PageHeader title="Compare" description="Compare campaigns, ad sets, ads, or time periods." />
      <EmptyState title="Not built yet" description="Comparison tooling ships in Phase 5." />
    </>
  );
}
