import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

export function WorkflowSettingsPanel() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Workflow settings</CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {[
          "Trigger: Hosted link or API",
          "Environment: Sandbox",
          "Manual review: Enabled",
          "Webhook delivery: Disabled",
        ].map((item) => (
          <div
            key={item}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm"
          >
            {item}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
