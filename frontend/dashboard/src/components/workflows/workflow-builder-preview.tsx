import { GitBranch, ShieldCheck, UserCheck, Workflow } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

const nodes = [
  ["Start", Workflow],
  ["Consent", ShieldCheck],
  ["Document check", UserCheck],
  ["Policy decision", GitBranch],
];

export function WorkflowBuilderPreview() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Workflow builder</CardTitle>
      </CardHeader>

      <CardContent>
        <div className="grid gap-4 md:grid-cols-4">
          {nodes.map(([label, Icon], index) => {
            const LucideIcon = Icon as typeof Workflow;

            return (
              <div key={label as string} className="relative">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-center">
                  <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                    <LucideIcon className="h-5 w-5" />
                  </div>
                  <p className="mt-4 text-sm font-medium">{label as string}</p>
                </div>

                {index < nodes.length - 1 ? (
                  <div className="hidden md:block absolute left-full top-1/2 h-px w-4 bg-slate-300" />
                ) : null}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
