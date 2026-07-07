import type { Metadata } from "next";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Clock3,
  Hourglass,
  ShieldCheck,
  TrendingUp,
  TriangleAlert,
  XCircle,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

export const metadata: Metadata = {
  title: "Overview",
};

const stats = [
  {
    id: "stat-total-verifications",
    label: "Total Verifications",
    value: "12,847",
    change: "+14.2%",
    trend: "up" as const,
    icon: ShieldCheck,
    description: "Across all policies this month",
  },
  {
    id: "stat-pending-review",
    label: "Pending Review",
    value: "38",
    change: "-5",
    trend: "down" as const,
    icon: Clock,
    description: "Requires manual attention",
  },
  {
    id: "stat-approval-rate",
    label: "Approval Rate",
    value: "94.1%",
    change: "+0.8%",
    trend: "up" as const,
    icon: TrendingUp,
    description: "Compared to prior period",
  },
  {
    id: "stat-failed-checks",
    label: "Failed Checks",
    value: "156",
    change: "+12",
    trend: "up-bad" as const,
    icon: TriangleAlert,
    description: "Fraud and mismatch events",
  },
];

const recentVerifications = [
  {
    id: "ver-001",
    subject: "James Okafor",
    email: "j.okafor@example.com",
    status: "approved",
    policy: "Standard KYC",
    createdAt: "2026-07-06 22:11",
  },
  {
    id: "ver-002",
    subject: "Amara Diallo",
    email: "amara.d@sample.io",
    status: "review",
    policy: "Enhanced KYC",
    createdAt: "2026-07-06 21:47",
  },
  {
    id: "ver-003",
    subject: "Lena Muller",
    email: "l.mueller@corp.de",
    status: "approved",
    policy: "Standard KYC",
    createdAt: "2026-07-06 21:03",
  },
  {
    id: "ver-004",
    subject: "Kevin Santos",
    email: "kevin.s@testco.com",
    status: "rejected",
    policy: "Standard KYC",
    createdAt: "2026-07-06 20:58",
  },
  {
    id: "ver-005",
    subject: "Priya Nair",
    email: "priya.n@example.in",
    status: "pending",
    policy: "Lite KYC",
    createdAt: "2026-07-06 20:30",
  },
];

const STATUS_CONFIG = {
  approved: { label: "Approved", variant: "success" as const, Icon: CheckCircle2 },
  rejected: { label: "Rejected", variant: "destructive" as const, Icon: XCircle },
  review: { label: "In Review", variant: "warning" as const, Icon: Hourglass },
  pending: { label: "Pending", variant: "secondary" as const, Icon: Hourglass },
};

export default function OverviewPage() {
  return (
    <div className="space-y-8 p-6 md:p-8">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Card className="overflow-hidden bg-linear-to-br from-primary/[0.07] via-background to-accent/[0.18]">
          <CardContent className="space-y-6 p-7">
            <Badge variant="info">
              <Activity className="h-3.5 w-3.5" />
              Trust operations summary
            </Badge>
            <div className="space-y-3">
              <h1 className="text-3xl font-semibold tracking-tight text-foreground">
                Your verification program is moving quickly and staying readable.
              </h1>
              <p className="max-w-2xl text-base leading-7 text-muted-foreground">
                Approval rates are stable, review backlog is down, and fraud-related failures are visible without drowning out the healthy signal.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button id="launch-verification-flow">Launch new flow</Button>
              <Button variant="outline" id="open-policy-builder">
                Open policy builder
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Today's focus</CardTitle>
            <CardDescription>
              The highest-value actions for the team right now.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl bg-secondary/70 p-4">
              <div className="text-sm font-semibold text-foreground">38 reviews pending</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Most are concentrated in enhanced KYC sessions from the last six hours.
              </div>
            </div>
            <div className="rounded-2xl bg-secondary/70 p-4">
              <div className="text-sm font-semibold text-foreground">Webhook latency normal</div>
              <div className="mt-1 text-sm text-muted-foreground">
                Median downstream delivery remains under 4 seconds across all destinations.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const isUp = stat.trend === "up";
          const isBad = stat.trend === "up-bad";

          return (
            <Card key={stat.id} id={stat.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardDescription className="text-xs font-medium uppercase tracking-wider">
                    {stat.label}
                  </CardDescription>
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10">
                    <Icon className="h-4 w-4 text-primary" strokeWidth={1.75} />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-semibold tracking-tight">{stat.value}</div>
                <div className="mt-1 flex items-center gap-1.5">
                  <span
                    className={
                      isBad
                        ? "flex items-center gap-0.5 text-xs font-medium text-destructive"
                        : isUp
                          ? "flex items-center gap-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400"
                          : "flex items-center gap-0.5 text-xs font-medium text-muted-foreground"
                    }
                  >
                    {isUp || isBad ? (
                      <ArrowUpRight className="h-3 w-3" />
                    ) : (
                      <Clock3 className="h-3 w-3" />
                    )}
                    {stat.change}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {stat.description}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Recent verifications</CardTitle>
              <CardDescription className="mt-0.5">
                Latest submissions across all projects
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" id="view-all-verifications">
              View all
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/50">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Subject
                </th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground md:table-cell">
                  Policy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Status
                </th>
                <th className="hidden px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground lg:table-cell">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {recentVerifications.map((verification) => {
                const config =
                  STATUS_CONFIG[verification.status as keyof typeof STATUS_CONFIG];

                return (
                  <tr
                    key={verification.id}
                    id={`row-${verification.id}`}
                    className="transition-colors hover:bg-secondary/35"
                  >
                    <td className="px-6 py-3.5">
                      <div className="font-medium text-foreground">{verification.subject}</div>
                      <div className="text-xs text-muted-foreground">{verification.email}</div>
                    </td>
                    <td className="hidden px-6 py-3.5 text-muted-foreground md:table-cell">
                      {verification.policy}
                    </td>
                    <td className="px-6 py-3.5">
                      <Badge variant={config.variant}>
                        <config.Icon className="h-3 w-3" />
                        {config.label}
                      </Badge>
                    </td>
                    <td className="hidden px-6 py-3.5 text-right text-muted-foreground lg:table-cell">
                      {verification.createdAt}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
