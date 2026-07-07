import type { Metadata } from "next";
import { Download, FileBarChart2, ShieldCheck, Users } from "lucide-react";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, PageHeader } from "@identitycore/ui";

export const metadata: Metadata = { title: "Reports" };

const reports = [
  { id: "rep-volume", name: "Verification volume", description: "Daily volume, outcomes, and queue trends by project.", freshness: "Updated 5 min ago" },
  { id: "rep-audit", name: "Audit export", description: "Reviewer actions, policy changes, and access events.", freshness: "Generated on demand" },
  { id: "rep-subjects", name: "Subject outcomes", description: "Exportable subject-level results with decision metadata.", freshness: "Updated hourly" },
];

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        description="Export verification outcomes, audit activity, and operational summaries."
        actions={<Button><Download className="h-4 w-4" />New export</Button>}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Verification outcomes</CardDescription>
            <CardTitle className="text-2xl">94.1%</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-3 text-sm text-muted-foreground">
            <ShieldCheck className="h-4 w-4 text-primary" />
            Approval rate across active policies this month.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Subjects exported</CardDescription>
            <CardTitle className="text-2xl">18,204</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-3 text-sm text-muted-foreground">
            <Users className="h-4 w-4 text-primary" />
            Includes CSV and JSON evidence summaries.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Audit retention</CardDescription>
            <CardTitle className="text-2xl">365d</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-3 text-sm text-muted-foreground">
            <FileBarChart2 className="h-4 w-4 text-primary" />
            Default retention for review and access events.
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {reports.map((report) => (
          <Card key={report.id}>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="text-base">{report.name}</CardTitle>
                <Badge variant="outline">{report.freshness}</Badge>
              </div>
              <CardDescription>{report.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full justify-between">
                Open report
                <Download className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
