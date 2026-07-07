import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Hourglass,
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
  PageHeader,
  StatCard,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@identitycore/ui";

export const metadata: Metadata = {
  title: "Overview",
};

const stats = [
  { label: "Total verifications", value: "12,847", change: "+14.2% vs last month", changeType: "positive" as const },
  { label: "Pending review", value: "38", change: "5 fewer than yesterday", changeType: "positive" as const },
  { label: "Approval rate", value: "94.1%", change: "+0.8% vs last month", changeType: "positive" as const },
  { label: "Failed checks", value: "156", change: "+12 vs last month", changeType: "negative" as const },
];

const recentVerifications = [
  { id: "ver-001", subject: "James Okafor", email: "j.okafor@example.com", status: "approved", policy: "Standard KYC", createdAt: "Jul 6, 2026 22:11" },
  { id: "ver-002", subject: "Amara Diallo", email: "amara.d@sample.io", status: "review", policy: "Enhanced KYC", createdAt: "Jul 6, 2026 21:47" },
  { id: "ver-003", subject: "Lena Muller", email: "l.mueller@corp.de", status: "approved", policy: "Standard KYC", createdAt: "Jul 6, 2026 21:03" },
  { id: "ver-004", subject: "Kevin Santos", email: "kevin.s@testco.com", status: "rejected", policy: "Standard KYC", createdAt: "Jul 6, 2026 20:58" },
  { id: "ver-005", subject: "Priya Nair", email: "priya.n@example.in", status: "pending", policy: "Lite KYC", createdAt: "Jul 6, 2026 20:30" },
];

const STATUS_CONFIG = {
  approved: { label: "Approved", variant: "success" as const },
  rejected: { label: "Rejected", variant: "destructive" as const },
  review: { label: "In review", variant: "warning" as const },
  pending: { label: "Pending", variant: "secondary" as const },
};

export default function OverviewPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Overview"
        description="Monitor verification volume, review backlog, and operational health."
        actions={
          <>
            <Button variant="outline" id="open-policy-builder">
              Manage policies
            </Button>
            <Button id="launch-verification-flow">New verification</Button>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-base font-semibold">Recent verifications</CardTitle>
              <CardDescription>Latest submissions across all policies</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild id="view-all-verifications">
              <Link href="/verifications/requests">
                View all
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Subject</TableHead>
                  <TableHead className="hidden md:table-cell">Policy</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden text-right lg:table-cell">Submitted</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentVerifications.map((row) => {
                  const config = STATUS_CONFIG[row.status as keyof typeof STATUS_CONFIG];
                  return (
                    <TableRow key={row.id} id={`row-${row.id}`}>
                      <TableCell>
                        <div className="font-medium">{row.subject}</div>
                        <div className="text-xs text-muted-foreground">{row.email}</div>
                      </TableCell>
                      <TableCell className="hidden text-muted-foreground md:table-cell">
                        {row.policy}
                      </TableCell>
                      <TableCell>
                        <Badge variant={config.variant}>{config.label}</Badge>
                      </TableCell>
                      <TableCell className="hidden text-right text-muted-foreground lg:table-cell">
                        {row.createdAt}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Action items</CardTitle>
            <CardDescription>Items requiring attention</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              href="/verifications/review"
              className="flex items-start gap-3 rounded-lg border border-border p-4 transition-colors hover:bg-muted/50"
            >
              <Hourglass className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              <div>
                <p className="text-sm font-medium">38 pending reviews</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Enhanced KYC sessions from the last 6 hours
                </p>
              </div>
            </Link>
            <div className="flex items-start gap-3 rounded-lg border border-border p-4">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
              <div>
                <p className="text-sm font-medium">Webhooks healthy</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Median delivery under 4 seconds
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg border border-border p-4">
              <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
              <div>
                <p className="text-sm font-medium">12 failed liveness checks</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Review fraud signals in logs
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
