import {
  GitBranch,
  KeyRound,
  Network,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";

export function FlowPreview() {
  return (
    <Card className="overflow-hidden rounded-[2rem] border-slate-200/80 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
      <CardHeader className="border-b bg-slate-50/70">
        <CardTitle className="text-base">Workflow execution</CardTitle>
        <CardDescription>
          From customer request to auditable result
        </CardDescription>
      </CardHeader>

      <CardContent className="p-6">
        <div className="space-y-3">
          {[
            ["Customer app", KeyRound],
            ["IdentityCore workflow", Workflow],
            ["Policy engine", GitBranch],
            ["Provider routing", Network],
            ["Trust decision", ShieldCheck],
          ].map(([label, Icon], index) => {
            const LucideIcon = Icon as typeof KeyRound;

            return (
              <div key={label as string}>
                <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                    <LucideIcon className="h-5 w-5" />
                  </div>

                  <div className="flex-1">
                    <p className="text-sm font-medium">{label as string}</p>
                  </div>

                  <Badge variant="secondary" className="rounded-full">
                    {index + 1}
                  </Badge>
                </div>

                {index < 4 ? (
                  <div className="ml-9 h-5 w-px bg-slate-200" />
                ) : null}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
