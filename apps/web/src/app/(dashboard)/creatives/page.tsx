import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function CreativesPage() {
  return (
    <>
      <PageHeader
        title="Creatives"
        description="Creative library — thumbnails, usage, performance, fatigue indicators."
      />
      <EmptyState
        title="Not built yet"
        description="Creative management ships in Phase 4 (image/video upload, creative creation)."
      />
    </>
  );
}
