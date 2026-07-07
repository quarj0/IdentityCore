import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Badge, Button, Card, CardContent, PageHeader, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@identitycore/ui";
import { AdminShell } from "@/components/admin-shell";
import { tenants } from "@/lib/admin-data";

export const metadata: Metadata = { title: "Tenants" };

export default function PlatformAdminTenantsPage() {
  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader title="Tenants" description="All organizations, plans, health posture, and current lifecycle state." />
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Organization</TableHead>
                  <TableHead>Tier</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">Region</TableHead>
                  <TableHead className="hidden lg:table-cell">Volume</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {tenants.map((tenant) => (
                  <TableRow key={tenant.id}>
                    <TableCell className="font-medium">{tenant.name}</TableCell>
                    <TableCell>{tenant.tier}</TableCell>
                    <TableCell><Badge variant={tenant.status === "Active" ? "success" : tenant.status === "Pending approval" ? "warning" : "destructive"}>{tenant.status}</Badge></TableCell>
                    <TableCell className="hidden md:table-cell text-muted-foreground">{tenant.region}</TableCell>
                    <TableCell className="hidden lg:table-cell text-muted-foreground">{tenant.verifications.toLocaleString()}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/tenants/${tenant.id}`}>
                          Open
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </Button>
                    </TableCell>
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
