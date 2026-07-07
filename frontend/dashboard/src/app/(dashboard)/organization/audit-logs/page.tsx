import type { Metadata } from "next";
import { Card, CardContent, Input, PageHeader, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@identitycore/ui";
import { Search } from "lucide-react";

export const metadata: Metadata = { title: "Audit Logs" };

const auditLogs = [
  { id: "audit-1", user: "Alex Carter", action: "API Key Created", target: "Production Key", ip: "192.168.1.1", date: "2026-07-06 23:59:12" },
  { id: "audit-2", user: "Sarah Connor", action: "Policy Updated", target: "Standard KYC", ip: "192.168.1.4", date: "2026-07-06 22:15:00" },
  { id: "audit-3", user: "Alex Carter", action: "Webhook Created", target: "https://api.acmecorp.com/hooks/identity", ip: "192.168.1.1", date: "2026-07-06 21:04:12" },
  { id: "audit-4", user: "David Miller", action: "Manual Review Approved", target: "James Okafor (req_1091)", ip: "192.168.1.8", date: "2026-07-06 19:47:00" },
  { id: "audit-5", user: "Alex Carter", action: "Team Member Invited", target: "elena.r@acme.com", ip: "192.168.1.1", date: "2026-07-05 14:12:00" },
];

export default function AuditLogsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit logs"
        description="Track operations and configuration changes made by your team."
      />

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input id="search-audit" placeholder="Search by user or action..." className="pl-8 h-9" />
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Target</th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground md:table-cell">IP Address</th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {auditLogs.map((log) => (
                <tr key={log.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-6 py-3.5 font-medium text-foreground">{log.user}</td>
                  <td className="px-6 py-3.5">{log.action}</td>
                  <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{log.target}</td>
                  <td className="hidden px-6 py-3.5 text-muted-foreground md:table-cell">{log.ip}</td>
                  <td className="px-6 py-3.5 text-right text-muted-foreground text-xs">{log.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
