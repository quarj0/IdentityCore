import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import { organizationBranding } from "@/features/organizations/mock-data";

export function OrganizationBrandingCard() {
  const items = [
    {
      label: "Logo",
      value: organizationBranding.logoStatus,
    },
    {
      label: "Portal theme",
      value: organizationBranding.portalTheme,
    },
    {
      label: "Email sender",
      value: organizationBranding.customEmailSender,
    },
  ];

  return (
    <SectionCard
      title="Branding"
      description="Organization verification portal branding and sender identity."
      action={
        <StatusPill tone="success">
          {organizationBranding.brandReview}
        </StatusPill>
      }
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-slate-200 bg-slate-950/40 p-4">
          <p className="text-sm text-slate-500">Primary color</p>

          <div className="mt-3 flex items-center gap-3">
            <div
              className="size-8 rounded-full ring-1 ring-white/20"
              style={{ backgroundColor: organizationBranding.primaryColor }}
              aria-hidden="true"
            />
            <p className="font-medium text-white">
              {organizationBranding.primaryColor}
            </p>
          </div>
        </div>

        <dl className="grid gap-3 sm:grid-cols-2">
          {items.map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-slate-200 bg-slate-950/40 p-4"
            >
              <dt className="text-sm text-slate-500">{item.label}</dt>
              <dd className="mt-2 font-medium text-white">{item.value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </SectionCard>
  );
}
