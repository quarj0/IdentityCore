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
  ["Identity verification", Fingerprint],
  ["Document intelligence", FileSearch],
  ["Biometric matching", ScanFace],
  ["Liveness checks", Radar],
  ["Consent records", ClipboardCheck],
  ["Audit trails", ScrollText],
  ["Risk scoring", Activity],
  ["Policy decisions", ListChecks],
  ["Provider orchestration", GitBranch],
  ["Workflow templates", Workflow],
  ["Webhooks", Send],
  ["Evidence reports", FileSearch],
] satisfies ReadonlyArray<readonly [string, LucideIcon]>;

export function ServiceGrid() {
  return (
    <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {services.map(([name, Icon]) => (
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
