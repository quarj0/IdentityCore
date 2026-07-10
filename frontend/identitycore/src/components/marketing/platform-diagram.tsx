import {
  Boxes,
  BrainCircuit,
  Database,
  KeyRound,
  Network,
  Shield,
} from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

export function PlatformDiagram() {
  return (
    <Card className="overflow-hidden rounded-4xl border-slate-200/80 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
      <CardHeader className="border-b bg-slate-50/70">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">IdentityCore stack</CardTitle>
            <CardDescription>
              Workflows, providers, APIs, and trust services
            </CardDescription>
          </div>
          <Badge className="rounded-full bg-blue-600">Infrastructure</Badge>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        <div className="rounded-3xl bg-slate-950 p-5 text-white">
          <div className="rounded-2xl border border-white/10 bg-white/10 p-4 text-center">
            <p className="text-sm font-medium">Workflow Engine</p>
            <p className="mt-1 text-xs text-slate-300">
              Policies · Events · Review · Automation
            </p>
          </div>

          <div className="my-5 grid gap-3 sm:grid-cols-3">
            {[
              ["Providers", Network],
              ["Identity APIs", KeyRound],
              ["Trust Services", BrainCircuit],
            ].map(([label, Icon]) => {
              const LucideIcon = Icon as typeof Network;

              return (
                <div
                  key={label as string}
                  className="rounded-2xl border border-white/10 bg-white/[0.06] p-4 text-center"
                >
                  <LucideIcon className="mx-auto mb-3 h-5 w-5 text-blue-300" />
                  <p className="text-xs font-medium">{label as string}</p>
                </div>
              );
            })}
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-blue-300">
              Connected systems
            </p>

            <div className="mt-3 flex flex-wrap gap-2">
              {[
                "Customer apps",
                "Government APIs",
                "Internal AI",
                "Object storage",
                "Webhooks",
              ].map((item) => (
                <span
                  key={item}
                  className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-200"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3">
          {[
            ["Data", Database],
            ["Security", Shield],
            ["Services", Boxes],
          ].map(([label, Icon]) => {
            const LucideIcon = Icon as typeof Database;

            return (
              <div
                key={label as string}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center"
              >
                <LucideIcon className="mx-auto mb-2 h-4 w-4 text-blue-600" />
                <p className="text-xs font-medium">{label as string}</p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
