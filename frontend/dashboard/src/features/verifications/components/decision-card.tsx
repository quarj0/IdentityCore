import { CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

export function DecisionCard() {
  return (
    <Card className="rounded-3xl border-blue-100 bg-blue-50 shadow-sm">
      <CardHeader>
        <CardTitle className="text-blue-950">Decision</CardTitle>
      </CardHeader>

      <CardContent>
        <div className="flex items-center gap-3">
          <CheckCircle2 className="h-8 w-8 text-blue-700" />
          <div>
            <p className="text-3xl font-semibold text-blue-950">Approved</p>
            <p className="mt-1 text-sm text-blue-800">
              Mock verification evidence passed policy checks.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
