import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, PageHeader } from "@identitycore/ui";
import { apiKeys, getStatusBadgeVariant } from "@/lib/mock-data";

export const metadata: Metadata = { title: "API Key Detail" };

export default async function ApiKeyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const apiKey = apiKeys.find((item) => item.id === id);

  if (!apiKey) notFound();

  return (
    <div className="space-y-6">
      <PageHeader
        title={apiKey.name}
        description={`${apiKey.prefix}••••••••${apiKey.suffix}`}
        actions={
          <>
            <Badge variant={getStatusBadgeVariant(apiKey.status)}>{apiKey.status}</Badge>
            <Button>{apiKey.status === "active" ? "Rotate key" : "Reissue key"}</Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Key metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Environment</span>
              <span className="font-medium text-foreground">{apiKey.environment}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Created</span>
              <span className="font-medium text-foreground">{apiKey.created}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Last used</span>
              <span className="font-medium text-foreground">{apiKey.lastUsed}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Scopes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {apiKey.scopes.map((scope) => (
              <div key={scope} className="rounded-lg border border-border px-4 py-3 text-sm font-mono text-foreground">
                {scope}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
