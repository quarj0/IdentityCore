import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

export function ProjectOverview() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Project overview</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-4 text-sm sm:grid-cols-2">
        <div>
          <p className="text-slate-500">Environment</p>
          <p className="mt-1 font-medium">Sandbox</p>
        </div>

        <div>
          <p className="text-slate-500">Status</p>
          <p className="mt-1 font-medium">Active</p>
        </div>

        <div>
          <p className="text-slate-500">Allowed origins</p>
          <p className="mt-1 font-medium">Not configured</p>
        </div>

        <div>
          <p className="text-slate-500">Created</p>
          <p className="mt-1 font-medium">Today</p>
        </div>
      </CardContent>
    </Card>
  );
}
