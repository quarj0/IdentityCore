import { Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

const requirements = [
  "Consent",
  "National ID or Passport",
  "Selfie capture",
  "Optional liveness",
  "Policy decision",
];

export function TemplateRequirements() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Requirements</CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {requirements.map((item) => (
          <div key={item} className="flex gap-3 text-sm text-slate-600">
            <Check className="mt-0.5 h-4 w-4 text-blue-600" />
            {item}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}