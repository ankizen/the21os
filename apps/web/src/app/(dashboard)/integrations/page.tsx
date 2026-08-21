import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/page-header";

const INTEGRATIONS = [
  {
    name: "Meta Ads",
    detail: "Marketing API v26.0 via facebook-business SDK",
    phase: "Phase 2",
  },
  {
    name: "Google Analytics 4",
    detail: "GA4 Data API + Admin API",
    phase: "Phase 5",
  },
  {
    name: "Claude / MCP",
    detail: "Tool access for the AI Command Center",
    phase: "Phase 6",
  },
];

export default function IntegrationsPage() {
  return (
    <>
      <PageHeader title="Integrations" description="Connection status for each external system." />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {INTEGRATIONS.map((integration) => (
          <Card key={integration.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{integration.name}</CardTitle>
              <Badge variant="outline" className="text-muted-foreground">
                Not connected
              </Badge>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{integration.detail}</p>
              <p className="mt-2 text-xs text-muted-foreground">Ships in {integration.phase}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
