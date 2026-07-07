import { Card, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

const teams = [
  ["Developers", "REST APIs, webhooks, sandbox projects, SDKs"],
  ["Operations", "Workflow templates, policies, dashboards"],
  ["Compliance", "Audit trails, consent, reports, retention"],
  ["Reviewers", "Manual review queues and explainable evidence"],
];

export function TeamCardGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {teams.map(([title, value]) => (
        <Card key={title} className="rounded-3xl p-2 shadow-sm">
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription className="leading-7">{value}</CardDescription>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}
