import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

const steps = ["Consent", "Document", "OCR", "Selfie", "Liveness", "Decision"];

export function TemplateWorkflowSteps() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Workflow steps</CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {steps.map((step, index) => (
          <div
            key={step}
            className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-50 text-sm font-semibold text-blue-700">
              {index + 1}
            </div>
            <p className="text-sm font-medium">{step}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}