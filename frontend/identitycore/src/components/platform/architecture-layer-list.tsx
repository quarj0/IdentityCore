const architectureLayers = [
  ["Applications", "Your apps, portals, dashboards, mobile apps"],
  ["IdentityCore APIs", "REST APIs, webhooks, SDKs, dashboard GraphQL"],
  ["Workflow Engine", "Policies, templates, automation, review routing"],
  [
    "Provider Layer",
    "IdentityCore services, external vendors, government APIs",
  ],
  ["Data Layer", "PostgreSQL, private object storage, audit records"],
];

export function ArchitectureLayerList() {
  return (
    <div className="space-y-4">
      {architectureLayers.map(([title, description], index) => (
        <div
          key={title}
          className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-sm font-semibold text-blue-700 ring-1 ring-blue-100">
              {index + 1}
            </div>
            <div>
              <h3 className="font-semibold">{title}</h3>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                {description}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
