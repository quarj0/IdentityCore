import type { LucideIcon } from "lucide-react";
import { Boxes } from "lucide-react";

interface Service {
  name: string;
  icon: LucideIcon;
}

const services: Service[] = [
  { name: "Identity verification", icon: Boxes },
  { name: "Document intelligence", icon: Boxes },
  { name: "Biometric matching", icon: Boxes },
  { name: "Liveness checks", icon: Boxes },
  { name: "Consent records", icon: Boxes },
  { name: "Audit trails", icon: Boxes },
  { name: "Risk scoring", icon: Boxes },
  { name: "Policy decisions", icon: Boxes },
  { name: "Provider orchestration", icon: Boxes },
  { name: "Workflow templates", icon: Boxes },
  { name: "Webhooks", icon: Boxes },
  { name: "Evidence reports", icon: Boxes },
];

export function ServiceGrid() {
  return (
    <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {services.map(({ name, icon: Icon }) => (
        <div
          key={name}
          className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
            <Icon className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium">{name}</span>
        </div>
      ))}
    </div>
  );
}
