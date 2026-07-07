"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  Layers3,
  ShieldAlert,
  Siren,
  TrendingUp,
  XCircle,
} from "lucide-react";
import {
  Badge,
  BrandMark,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  ThemeToggle,
} from "@identitycore/ui";

const orgs = [
  { id: "org-1", name: "Acme Corporation", tier: "Growth", status: "Active", verifications: 1420 },
  { id: "org-2", name: "CyberDyne Systems", tier: "Enterprise", status: "Pending approval", verifications: 0 },
  { id: "org-3", name: "Globex Corporation", tier: "Developer", status: "Active", verifications: 84 },
  { id: "org-4", name: "Initech", tier: "Growth", status: "Suspended", verifications: 410 },
];

const statCards = [
  { label: "Active tenants", value: "248", description: "Across all regions", icon: Building2 },
  { label: "30d verification volume", value: "142,847", description: "Up 11.8% month-over-month", icon: TrendingUp },
  { label: "Escalated incidents", value: "4", description: "Two awaiting response", icon: Siren },
];

export default function PlatformAdminPage() {
  const [activeView, setActiveView] = useState("tenants");

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <BrandMark subtitle="Platform admin" />
          <div className="flex items-center gap-3">
            <Badge variant="destructive" className="hidden sm:inline-flex">
              <ShieldAlert className="h-3.5 w-3.5" />
              Internal use only
            </Badge>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-8 px-6 py-8 lg:px-8">
        <section className="space-y-4">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            Platform trust operations
          </h1>
          <p className="max-w-3xl text-muted-foreground leading-7">
            Current risk, account health, and approval backlog — all visible without hunting.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline">Review incidents</Button>
            <Button>Approve queue</Button>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <Card key={card.label}>
                <CardHeader className="space-y-4">
                  <div className="flex items-center justify-between">
                    <CardDescription className="text-xs font-semibold uppercase tracking-wider">
                      {card.label}
                    </CardDescription>
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>
                  <div>
                    <CardTitle className="text-2xl">{card.value}</CardTitle>
                    <CardDescription className="mt-2">{card.description}</CardDescription>
                  </div>
                </CardHeader>
              </Card>
            );
          })}
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)]">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <CardTitle className="text-lg">Organization accounts</CardTitle>
                  <CardDescription>
                    Approvals, suspensions, and current customer health.
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant={activeView === "tenants" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveView("tenants")}
                  >
                    Tenant queue
                  </Button>
                  <Button
                    variant={activeView === "risk" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveView("risk")}
                  >
                    Risk review
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {orgs.map((org) => (
                <div
                  key={org.id}
                  className="flex flex-col gap-4 rounded-lg border border-border p-4 transition-colors hover:bg-muted/30 lg:flex-row lg:items-center"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Building2 className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold text-foreground">
                        {org.name}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {org.tier} plan · {org.verifications.toLocaleString()} verifications
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    <Badge
                      variant={
                        org.status === "Active"
                          ? "success"
                          : org.status === "Pending approval"
                            ? "warning"
                            : "destructive"
                      }
                    >
                      {org.status}
                    </Badge>
                    {org.status === "Pending approval" ? (
                      <>
                        <Button size="sm">Approve</Button>
                        <Button size="sm" variant="outline">
                          Reject
                        </Button>
                      </>
                    ) : (
                      <Button size="sm" variant="outline">
                        Open account
                      </Button>
                    )}
                  </div>
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
                  <XCircle className="h-4 w-4 shrink-0" />
                  One tenant awaiting final suspension decision
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Ops principles</CardTitle>
                <CardDescription>What this console is optimizing for.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
                {[
                  "Put urgent account state in the first viewport.",
                  "Keep approvals and escalations one action away.",
                  "Make platform health legible without decorative noise.",
                ].map((principle) => (
                  <div key={principle} className="flex gap-3">
                    <Layers3 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    {principle}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}
