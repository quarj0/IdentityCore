import type { Metadata } from "next";
import { AlertTriangle, CheckCircle2, Layers3, Siren, TrendingUp } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, StatCard } from "@identitycore/ui";
import { AdminPageFrame } from "@/components/admin-page-frame";
import { tenants } from "@/lib/admin-data";

export const metadata: Metadata = { title: "Overview" };

const statCards = [
  { label: "Active tenants", value: "248", change: "Across all regions", changeType: "neutral" as const },
  { label: "30d verification volume", value: "142,847", change: "+11.8% month-over-month", changeType: "positive" as const },
  { label: "Escalated incidents", value: "4", change: "Two awaiting response", changeType: "negative" as const },
];

export default function PlatformAdminOverviewPage() {
  return (
    <AdminPageFrame
      title="Overview"
      description="Current risk, account health, and approval backlog across the platform."
      actions={
        <>
          <Button variant="outline">Review incidents</Button>
          <Button>Approve queue</Button>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-3">
        {statCards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Organization accounts</CardTitle>
            <CardDescription>Approvals, suspensions, and current customer health.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {tenants.map((org) => (
              <div key={org.id} className="flex flex-col gap-4 rounded-lg border border-border p-4 lg:flex-row lg:items-center">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold text-foreground">{org.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {org.tier} plan · {org.verifications.toLocaleString()} verifications · {org.region}
                  </div>
                </div>
                <Button variant="outline" size="sm">Open account</Button>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Platform status</CardTitle>
              <CardDescription>Current trust and service posture.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3 rounded-lg bg-emerald-500/10 p-3 text-sm text-emerald-700 dark:text-emerald-300">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                Review systems and webhooks operational
              </div>
              <div className="flex items-center gap-3 rounded-lg bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                Elevated manual review volume in West Africa queue
              </div>
              <div className="flex items-center gap-3 rounded-lg bg-rose-500/10 p-3 text-sm text-rose-700 dark:text-rose-300">
                <Siren className="h-4 w-4 shrink-0" />
                One tenant awaiting final suspension decision
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ops principles</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
              <div className="flex gap-3"><Layers3 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />Put urgent account state in the first viewport.</div>
              <div className="flex gap-3"><TrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-primary" />Make degraded provider health legible without decorative noise.</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminPageFrame>
  );
}
