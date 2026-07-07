import type { Metadata } from "next";
import Link from "next/link";
import {
  CheckCircle2,
  XCircle,
  Hourglass,
  Clock,
  Search,
  Plus,
  ExternalLink,
} from "lucide-react";
import {
  Card,
  CardContent,
  Badge,
  Button,
  Input,
  PageHeader,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "Verification Requests" };

const STATUS_CONFIG = {
  approved: { label: "Approved", variant: "success" as const, Icon: CheckCircle2 },
  rejected: { label: "Rejected", variant: "destructive" as const, Icon: XCircle },
  review: { label: "In review", variant: "warning" as const, Icon: Hourglass },
  pending: { label: "Pending", variant: "secondary" as const, Icon: Clock },
  expired: { label: "Expired", variant: "outline" as const, Icon: Clock },
};

const requests = [
  { id: "REQ-1091", subject: "James Okafor", email: "j.okafor@example.com", policy: "Standard KYC", status: "approved", created: "Jul 6, 2026", expires: "Jul 13, 2026" },
  { id: "REQ-1090", subject: "Amara Diallo", email: "amara.d@sample.io", policy: "Enhanced KYC", status: "review", created: "Jul 6, 2026", expires: "Jul 13, 2026" },
  { id: "REQ-1089", subject: "Lena Müller", email: "l.mueller@corp.de", policy: "Standard KYC", status: "approved", created: "Jul 5, 2026", expires: "Jul 12, 2026" },
  { id: "REQ-1088", subject: "Kevin Santos", email: "kevin.s@testco.com", policy: "Standard KYC", status: "rejected", created: "Jul 5, 2026", expires: "Jul 12, 2026" },
  { id: "REQ-1087", subject: "Priya Nair", email: "priya.n@example.in", policy: "Lite KYC", status: "pending", created: "Jul 5, 2026", expires: "Jul 12, 2026" },
  { id: "REQ-1086", subject: "Chen Wei", email: "c.wei@techfirm.cn", policy: "Standard KYC", status: "approved", created: "Jul 4, 2026", expires: "Jul 11, 2026" },
  { id: "REQ-1085", subject: "Sofia Russo", email: "sofia.r@italco.it", policy: "Enhanced KYC", status: "approved", created: "Jul 4, 2026", expires: "Jul 11, 2026" },
  { id: "REQ-1084", subject: "Marcus Bello", email: "m.bello@ng.co", policy: "Standard KYC", status: "expired", created: "Jun 29, 2026", expires: "Jul 6, 2026" },
];

export default function VerificationRequestsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Verification requests"
        description="All verification requests across your organization."
        actions={
          <Button asChild id="create-verification-request">
            <Link href="/verifications/create">
              <Plus className="h-4 w-4" />
              New request
            </Link>
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input id="search-requests" placeholder="Search by name or email" className="h-9 pl-9" />
        </div>
        <Select>
          <SelectTrigger id="filter-status" className="h-9 w-[140px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="review">In review</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
          </SelectContent>
        </Select>
        <Select>
          <SelectTrigger id="filter-policy" className="h-9 w-[160px]">
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

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Request ID</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead className="hidden md:table-cell">Policy</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="hidden lg:table-cell">Created</TableHead>
                <TableHead className="hidden xl:table-cell">Expires</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.map((r) => {
                const cfg = STATUS_CONFIG[r.status as keyof typeof STATUS_CONFIG];
                return (
                  <TableRow key={r.id} id={`request-row-${r.id}`}>
                    <TableCell className="font-mono text-xs text-muted-foreground">{r.id}</TableCell>
                    <TableCell>
                      <div className="font-medium">{r.subject}</div>
                      <div className="text-xs text-muted-foreground">{r.email}</div>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground md:table-cell">{r.policy}</TableCell>
                    <TableCell>
                      <Badge variant={cfg.variant}>{cfg.label}</Badge>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground lg:table-cell">{r.created}</TableCell>
                    <TableCell className="hidden text-muted-foreground xl:table-cell">{r.expires}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" className="h-8 w-8" asChild id={`view-request-${r.id}`}>
                        <Link href={`/verifications/requests/${r.id}`}>
                          <ExternalLink className="h-3.5 w-3.5" />
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
