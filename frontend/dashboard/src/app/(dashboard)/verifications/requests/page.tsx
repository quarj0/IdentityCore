import type { Metadata } from "next";
import {
  CheckCircle2,
  XCircle,
  Hourglass,
  Clock,
  Search,
  Filter,
  Plus,
  ExternalLink,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "Verification Requests" };

const STATUS_CONFIG = {
  approved: { label: "Approved", variant: "success" as const, Icon: CheckCircle2 },
  rejected: { label: "Rejected", variant: "destructive" as const, Icon: XCircle },
  review: { label: "In Review", variant: "warning" as const, Icon: Hourglass },
  pending: { label: "Pending", variant: "secondary" as const, Icon: Clock },
  expired: { label: "Expired", variant: "outline" as const, Icon: Clock },
};

const requests = [
  { id: "REQ-1091", subject: "James Okafor", email: "j.okafor@example.com", policy: "Standard KYC", status: "approved", created: "2026-07-06", expires: "2026-07-13" },
  { id: "REQ-1090", subject: "Amara Diallo", email: "amara.d@sample.io", policy: "Enhanced KYC", status: "review", created: "2026-07-06", expires: "2026-07-13" },
  { id: "REQ-1089", subject: "Lena Müller", email: "l.mueller@corp.de", policy: "Standard KYC", status: "approved", created: "2026-07-05", expires: "2026-07-12" },
  { id: "REQ-1088", subject: "Kevin Santos", email: "kevin.s@testco.com", policy: "Standard KYC", status: "rejected", created: "2026-07-05", expires: "2026-07-12" },
  { id: "REQ-1087", subject: "Priya Nair", email: "priya.n@example.in", policy: "Lite KYC", status: "pending", created: "2026-07-05", expires: "2026-07-12" },
  { id: "REQ-1086", subject: "Chen Wei", email: "c.wei@techfirm.cn", policy: "Standard KYC", status: "approved", created: "2026-07-04", expires: "2026-07-11" },
  { id: "REQ-1085", subject: "Sofia Russo", email: "sofia.r@italco.it", policy: "Enhanced KYC", status: "approved", created: "2026-07-04", expires: "2026-07-11" },
  { id: "REQ-1084", subject: "Marcus Bello", email: "m.bello@ng.co", policy: "Standard KYC", status: "expired", created: "2026-06-29", expires: "2026-07-06" },
];

export default function VerificationRequestsPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Verification Requests</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            All verification requests across your organization.
          </p>
        </div>
        <Button id="create-verification-request" className="gap-2 self-start sm:self-auto">
          <Plus className="h-4 w-4" />
          New Request
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input id="search-requests" placeholder="Search by name or email…" className="pl-8 h-9" />
        </div>
        <Select>
          <SelectTrigger id="filter-status" className="w-36 h-9">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="review">In Review</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
          </SelectContent>
        </Select>
        <Select>
          <SelectTrigger id="filter-policy" className="w-40 h-9">
            <SelectValue placeholder="All policies" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All policies</SelectItem>
            <SelectItem value="standard">Standard KYC</SelectItem>
            <SelectItem value="enhanced">Enhanced KYC</SelectItem>
            <SelectItem value="lite">Lite KYC</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Subject</th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground md:table-cell">Policy</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Status</th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground lg:table-cell">Created</th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground xl:table-cell">Expires</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {requests.map((r) => {
                  const cfg = STATUS_CONFIG[r.status as keyof typeof STATUS_CONFIG];
                  return (
                    <tr key={r.id} id={`request-row-${r.id}`} className="transition-colors hover:bg-muted/30">
                      <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{r.id}</td>
                      <td className="px-6 py-3.5">
                        <div className="font-medium">{r.subject}</div>
                        <div className="text-xs text-muted-foreground">{r.email}</div>
                      </td>
                      <td className="hidden px-6 py-3.5 text-muted-foreground md:table-cell">{r.policy}</td>
                      <td className="px-6 py-3.5">
                        <Badge variant={cfg.variant} className="gap-1">
                          <cfg.Icon className="h-3 w-3" />
                          {cfg.label}
                        </Badge>
                      </td>
                      <td className="hidden px-6 py-3.5 text-muted-foreground lg:table-cell">{r.created}</td>
                      <td className="hidden px-6 py-3.5 text-muted-foreground xl:table-cell">{r.expires}</td>
                      <td className="px-6 py-3.5">
                        <Button variant="ghost" size="icon" className="h-7 w-7" id={`view-request-${r.id}`}>
                          <ExternalLink className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
