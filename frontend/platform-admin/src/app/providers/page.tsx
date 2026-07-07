import type { Metadata } from "next";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { AdminPageFrame } from "@/components/admin-page-frame";
import { providers } from "@/lib/admin-data";

export const metadata: Metadata = { title: "Providers" };

export default function PlatformAdminProvidersPage() {
  return (
    <AdminPageFrame title="Providers" description="Monitor provider health, latency, and operational caveats.">
      <div className="grid gap-4 lg:grid-cols-3">
        {providers.map((provider) => (
          <Card key={provider.name}>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="text-base">{provider.name}</CardTitle>
                <Badge variant={provider.status === "Operational" ? "success" : "warning"}>{provider.status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <div>Latency: {provider.latency}</div>
              <div>{provider.note}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </AdminPageFrame>
  );
}
