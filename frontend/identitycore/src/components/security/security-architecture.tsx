import {
  Database,
  FileLock2,
  GitBranch,
  KeyRound,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";

const layers = [
  {
    title: "Tenant boundary",
    description: "Every request is scoped to an organization workspace.",
    icon: ShieldCheck,
  },
  {
    title: "Policy layer",
    description: "Versioned policies decide what happens and why.",
    icon: GitBranch,
  },
  {
    title: "Access layer",
    description: "Roles, API keys, and permissions limit actions.",
    icon: KeyRound,
  },
  {
    title: "Private media",
    description: "Documents, selfies, and reports use signed access.",
    icon: FileLock2,
  },
  {
    title: "Data layer",
    description: "Identity data, evidence, and audit records are separated.",
    icon: Database,
  },
  {
    title: "Audit layer",
    description: "Sensitive actions produce traceable audit events.",
    icon: LockKeyhole,
  },
];

export function SecurityArchitecture() {
  return (
    <div className="rounded-4xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-3 sm:grid-cols-2">
        {layers.map((layer) => {
          const Icon = layer.icon;

          return (
            <div
              key={layer.title}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </div>

                <div>
                  <p className="text-sm font-semibold">{layer.title}</p>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    {layer.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
