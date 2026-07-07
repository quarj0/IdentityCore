import { Check } from "lucide-react";

const capabilities = [
  "Use IdentityCore services or bring your own providers",
  "Create reusable workflows and templates",
  "Apply country, risk, and organization-specific policies",
  "Route cases to manual review when needed",
  "Receive outcomes through APIs, webhooks, or dashboards",
  "Maintain audit trails and governance records",
];

export function IndustryUseCase() {
  return (
    <div className="grid gap-3">
      {capabilities.map((item) => (
        <div
          key={item}
          className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4"
        >
          <Check className="h-5 w-5 text-blue-300" />
          <span className="text-sm font-medium text-slate-100">{item}</span>
        </div>
      ))}
    </div>
  );
}
