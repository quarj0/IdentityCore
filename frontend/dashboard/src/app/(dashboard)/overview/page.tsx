import type { Metadata } from "next";
import {
  ShieldCheck,
  Clock,
  TrendingUp,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  XCircle,
  Hourglass,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Badge,
  Button,
} from "@identitycore/ui";

export const metadata: Metadata = {
  title: "Overview",
};

/* ─── Mock data ─────────────────────────────────────────── */
const stats = [
  {
    id: "stat-total-verifications",
    label: "Total Verifications",
    value: "12,847",
    change: "+14.2%",
    trend: "up" as const,
    icon: ShieldCheck,
    description: "Last 30 days",
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
    description: "Last 30 days",
  },
  {
    id: "stat-failed-checks",
    label: "Failed Checks",
    value: "156",
    change: "+12",
    trend: "up-bad" as const,
    icon: AlertTriangle,
    description: "Last 30 days",
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
    subject: "Lena Müller",
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

/* ─── Overview Page ─────────────────────────────────────── */
export default function OverviewPage() {
  return (
    <div className="p-6 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Overview</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your verification activity for the last 30 days.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const isUp = stat.trend === "up";
          const isBad = stat.trend === "up-bad";
          return (
            <Card key={stat.id} id={stat.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription className="text-xs font-medium uppercase tracking-wider">
                    {stat.label}
                  </CardDescription>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                    <Icon className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tracking-tight">{stat.value}</div>
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
                      <ArrowDownRight className="h-3 w-3" />
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

      {/* Recent Verifications */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Recent Verifications</CardTitle>
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
              <tr className="border-b border-border bg-muted/40">
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
              {recentVerifications.map((v) => {
                const cfg = STATUS_CONFIG[v.status as keyof typeof STATUS_CONFIG];
                return (
                  <tr
                    key={v.id}
                    id={`row-${v.id}`}
                    className="transition-colors hover:bg-muted/30"
                  >
                    <td className="px-6 py-3.5">
                      <div className="font-medium text-foreground">{v.subject}</div>
                      <div className="text-xs text-muted-foreground">{v.email}</div>
                    </td>
                    <td className="hidden px-6 py-3.5 text-muted-foreground md:table-cell">
                      {v.policy}
                    </td>
                    <td className="px-6 py-3.5">
                      <Badge variant={cfg.variant} className="gap-1">
                        <cfg.Icon className="h-3 w-3" />
                        {cfg.label}
                      </Badge>
                    </td>
                    <td className="hidden px-6 py-3.5 text-right text-muted-foreground lg:table-cell">
                      {v.createdAt}
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
