import type { Metadata } from "next";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, PageHeader, Switch } from "@identitycore/ui";
import { AdminShell } from "@/components/admin-shell";

export const metadata: Metadata = { title: "Settings" };

export default function PlatformAdminSettingsPage() {
  return (
    <AdminShell>
      <div className="max-w-4xl space-y-6">
        <PageHeader title="Settings" description="Operational controls, internal notifications, and platform-wide trust defaults." />
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Operational defaults</CardTitle>
            <CardDescription>Global settings for queues and alerting.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="review-sla">Manual review SLA (minutes)</Label>
                <Input id="review-sla" defaultValue="30" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="incident-webhook">Incident webhook URL</Label>
                <Input id="incident-webhook" defaultValue="https://ops.identitycore.internal/hooks/incidents" />
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border p-4">
              <div>
                <div className="font-medium text-foreground">Auto-escalate degraded providers</div>
                <div className="text-sm text-muted-foreground">Open an internal incident when error budgets are crossed.</div>
              </div>
              <Switch checked />
            </div>
            <Button>Save settings</Button>
          </CardContent>
        </Card>
      </div>
    </AdminShell>
  );
}
