import { SectionCard } from "@/components/shared/section-card";

const apiTraffic = [
  {
    label: "Public API",
    value: "18.4M",
    width: "82%",
  },
  {
    label: "Verification API",
    value: "11.7M",
    width: "64%",
  },
  {
    label: "Webhook delivery",
    value: "5.8M",
    width: "41%",
  },
  {
    label: "Admin API",
    value: "2.3M",
    width: "22%",
  },
];

export function ApiTrafficCard() {
  return (
    <SectionCard
      title="API traffic"
      description="Requests processed across IdentityCore APIs in the last 30 days."
    >
      <div className="space-y-5">
        {apiTraffic.map((item) => (
          <div key={item.label}>
            <div className="flex items-center justify-between gap-4 text-sm">
              <span className="font-medium text-slate-200">{item.label}</span>
              <span className="text-slate-400">{item.value}</span>
            </div>

            <div className="mt-2 h-2 rounded-full bg-white/10">
              <div
                className="h-2 rounded-full bg-cyan-300"
                style={{ width: item.width }}
              />
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}
