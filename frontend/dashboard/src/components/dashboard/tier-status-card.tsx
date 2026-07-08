import { ShieldCheck } from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { workspace } from "@/data/mock-dashboard";

export function TierStatusCard() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Workspace status</CardTitle>
          <Badge variant="secondary" className="rounded-full">
            {workspace.environment}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="flex gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <ShieldCheck className="h-5 w-5" />
          </div>

          <div>
            <p className="font-semibold">{workspace.tier}</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Complete onboarding to request production approval.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
