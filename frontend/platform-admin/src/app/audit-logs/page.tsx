import type { Metadata } from "next";
import { Badge, Card, CardContent, PageHeader, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@identitycore/ui";
import { AdminShell } from "@/components/admin-shell";

export const metadata: Metadata = { title: "Audit Logs" };

const entries = [
  { actor: "ops@identitycore.com", action: "Approved organization", target: "CyberDyne Systems", time: "2026-07-06 21:10", severity: "Info" },
  { actor: "risk@identitycore.com", action: "Suspended tenant", target: "Initech", time: "2026-07-06 18:14", severity: "Warning" },
  { actor: "platform@identitycore.com", action: "Rotated webhook secret", target: "Acme Corporation", time: "2026-07-06 16:52", severity: "Info" },
];

export default function PlatformAdminAuditLogsPage() {
  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader title="Audit logs" description="Platform-wide administrative actions across all tenants and internal operators." />
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Actor</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Severity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={`${entry.actor}-${entry.time}`}>
                    <TableCell className="font-medium">{entry.actor}</TableCell>
                    <TableCell>{entry.action}</TableCell>
                    <TableCell className="text-muted-foreground">{entry.target}</TableCell>
                    <TableCell className="text-muted-foreground">{entry.time}</TableCell>
                    <TableCell><Badge variant={entry.severity === "Warning" ? "warning" : "outline"}>{entry.severity}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </AdminShell>
  );
}
