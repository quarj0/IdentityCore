import type { Metadata } from "next";
import {
  CheckCircle2,
  XCircle,
  Hourglass,
  Clock,
  Search,
  ExternalLink,
  User,
} from "lucide-react";
import {
  Card,
  CardContent,
  Badge,
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Avatar,
  AvatarFallback,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "Verification Subjects" };

const subjects = [
  { id: "sub-001", name: "James Okafor", email: "j.okafor@example.com", verifications: 2, lastVerified: "2026-07-06", status: "verified" },
  { id: "sub-002", name: "Amara Diallo", email: "amara.d@sample.io", verifications: 1, lastVerified: "2026-07-06", status: "review" },
  { id: "sub-003", name: "Lena Müller", email: "l.mueller@corp.de", verifications: 3, lastVerified: "2026-07-05", status: "verified" },
  { id: "sub-004", name: "Kevin Santos", email: "kevin.s@testco.com", verifications: 1, lastVerified: "2026-07-05", status: "rejected" },
  { id: "sub-005", name: "Priya Nair", email: "priya.n@example.in", verifications: 1, lastVerified: "2026-07-05", status: "pending" },
  { id: "sub-006", name: "Chen Wei", email: "c.wei@techfirm.cn", verifications: 2, lastVerified: "2026-07-04", status: "verified" },
  { id: "sub-007", name: "Sofia Russo", email: "sofia.r@italco.it", verifications: 4, lastVerified: "2026-07-04", status: "verified" },
];

const STATUS_MAP = {
  verified: { label: "Verified", variant: "success" as const, Icon: CheckCircle2 },
  rejected: { label: "Rejected", variant: "destructive" as const, Icon: XCircle },
  review: { label: "In Review", variant: "warning" as const, Icon: Hourglass },
  pending: { label: "Pending", variant: "secondary" as const, Icon: Clock },
};

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function SubjectsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Subjects</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Individuals who have been submitted for verification.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input id="search-subjects" placeholder="Search subjects…" className="pl-8 h-9" />
        </div>
        <Select>
          <SelectTrigger id="filter-subject-status" className="w-36 h-9">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="verified">Verified</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="review">In Review</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Status</th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground md:table-cell">Verifications</th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground lg:table-cell">Last Verified</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {subjects.map((s) => {
                const cfg = STATUS_MAP[s.status as keyof typeof STATUS_MAP];
                return (
                  <tr key={s.id} id={`subject-row-${s.id}`} className="transition-colors hover:bg-muted/30">
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-7 w-7">
                          <AvatarFallback className="text-xs">{initials(s.name)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium">{s.name}</div>
                          <div className="text-xs text-muted-foreground">{s.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-3.5">
                      <Badge variant={cfg.variant} className="gap-1">
                        <cfg.Icon className="h-3 w-3" />
                        {cfg.label}
                      </Badge>
                    </td>
                    <td className="hidden px-6 py-3.5 text-muted-foreground md:table-cell">{s.verifications}</td>
                    <td className="hidden px-6 py-3.5 text-muted-foreground lg:table-cell">{s.lastVerified}</td>
                    <td className="px-6 py-3.5">
                      <Button variant="ghost" size="icon" className="h-7 w-7" id={`view-subject-${s.id}`}>
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Button>
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
