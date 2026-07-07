"use client";

import React, { useState } from "react";
import { ShieldAlert, CheckCircle2, XCircle, Building, AlertTriangle, Fingerprint, Activity } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Badge } from "@identitycore/ui";

const orgs = [
  { id: "org-1", name: "Acme Corporation", tier: "Growth", status: "Active", verifications: 1420 },
  { id: "org-2", name: "CyberDyne Systems", tier: "Enterprise", status: "Pending Approval", verifications: 0 },
  { id: "org-3", name: "Globex Corporation", tier: "Developer", status: "Active", verifications: 84 },
  { id: "org-4", name: "Initech", tier: "Growth", status: "Suspended", verifications: 410 },
];

export default function PlatformAdminPage() {
  const [activeTab, setActiveTab] = useState("orgs");

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <header className="px-6 h-16 border-b border-border bg-white dark:bg-slate-950 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-950 text-white">
            <Fingerprint className="h-4.5 w-4.5" />
          </div>
          <span className="font-semibold text-sm tracking-tight text-slate-900 dark:text-white">Platform Admin</span>
        </div>
        <Badge variant="destructive" className="text-[10px]">Internal Operations</Badge>
      </header>

      {/* Main Grid */}
      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="text-xs uppercase tracking-wider">Total Tenants</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-extrabold">248</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="text-xs uppercase tracking-wider">Platform Verifications (30d)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-extrabold">142,847</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="text-xs uppercase tracking-wider">System Status</CardDescription>
            </CardHeader>
            <CardContent>
              <Badge variant="success" className="text-xs font-semibold">All Systems Operational</Badge>
            </CardContent>
          </Card>
        </div>

        {/* Organizations Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Organization Accounts</CardTitle>
            <CardDescription className="text-xs">Manage tiers and approve new customer tenants.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground font-semibold">Organization</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground font-semibold">Tier</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground font-semibold">Verifications</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground font-semibold">Status</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {orgs.map((org) => (
                  <tr key={org.id} className="transition-colors hover:bg-muted/30">
                    <td className="px-6 py-3.5 flex items-center gap-2">
                      <Building className="h-4 w-4 text-muted-foreground" />
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{org.name}</span>
                    </td>
                    <td className="px-6 py-3.5 text-muted-foreground">{org.tier}</td>
                    <td className="px-6 py-3.5 text-muted-foreground font-mono">{org.verifications}</td>
                    <td className="px-6 py-3.5">
                      <Badge variant={org.status === "Active" ? "success" : org.status.includes("Pending") ? "warning" : "destructive"}>
                        {org.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-3.5 text-right flex gap-2 justify-end">
                      {org.status.includes("Pending") && (
                        <>
                          <Button size="sm" id={`approve-${org.id}`} className="bg-emerald-600 hover:bg-emerald-700 text-white">Approve</Button>
                          <Button size="sm" variant="destructive" id={`reject-${org.id}`}>Reject</Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
