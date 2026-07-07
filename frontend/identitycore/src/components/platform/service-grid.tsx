import { Boxes } from "lucide-react";

const services = [
  "Identity verification",
  "Document intelligence",
  "Biometric matching",
  "Liveness checks",
  "Consent records",
  "Audit trails",
  "Risk scoring",
  "Policy decisions",
  "Provider orchestration",
  "Workflow templates",
  "Webhooks",
  "Evidence reports",
];

export function ServiceGrid() {
  return (
    <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {services.map((service) => (
        <div
          key={service}
          className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
            <Boxes className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium">{service}</span>
        </div>
      ))}
    </div>
  );
}
