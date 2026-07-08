import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

export function ProjectIntegrations() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Integration settings</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-3">
        {[
          "Webhook endpoints",
          "API keys",
          "Allowed origins",
          "Environment variables",
        ].map((item) => (
          <div
            key={item}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm font-medium"
          >
            {item}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
