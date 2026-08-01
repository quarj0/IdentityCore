import {
  Activity,
  ClipboardCheck,
  FileSearch,
  Fingerprint,
  GitBranch,
  ListChecks,
  Radar,
  ScanFace,
  ScrollText,
  Send,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const services = [
  { name: "Identity verification", icon: Fingerprint },
  { name: "Document intelligence", icon: FileSearch },
  { name: "Biometric matching", icon: ScanFace },
  { name: "Liveness checks", icon: Radar },
  { name: "Consent records", icon: ClipboardCheck },
  { name: "Audit trails", icon: ScrollText },
  { name: "Risk scoring", icon: Activity },
  { name: "Policy decisions", icon: ListChecks },
  { name: "Provider orchestration", icon: GitBranch },
  { name: "Workflow templates", icon: Workflow },
  { name: "Webhooks", icon: Send },
  { name: "Evidence reports", icon: FileSearch },
] satisfies ReadonlyArray<{ name: string; icon: LucideIcon }>;

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
