import type { AdminModuleConfig, AdminRecord } from "@/components/admin-module/admin-module-types";

export const featureFlagRecords: AdminRecord[] = [
  {
    id: "flag_passive_liveness",
    title: "Passive Liveness Beta",
    subtitle: "Gradual rollout for passive liveness checks in verification workflows.",
    status: "Enabled",
    statusTone: "success",
    primaryMeta: "35% rollout",
    secondaryMeta: "Beta",
    tertiaryMeta: "12 organizations",
    owner: "AI Platform",
    updatedAt: "2026-07-09",
    href: "/feature-flags/flag_passive_liveness",
  },
  {
    id: "flag_new_review_console",
    title: "New Review Console",
    subtitle: "Improved reviewer workspace with quality checklist and evidence panel.",
    status: "Enabled",
    statusTone: "success",
    primaryMeta: "80% rollout",
    secondaryMeta: "Stable",
    tertiaryMeta: "Internal users",
    owner: "Product Platform",
    updatedAt: "2026-07-08",
    href: "/feature-flags/flag_new_review_console",
  },
  {
    id: "flag_provider_failover",
    title: "Provider Failover V2",
    subtitle: "Advanced provider failover routing for OCR and face providers.",
    status: "Disabled",
    statusTone: "neutral",
    primaryMeta: "0% rollout",
    secondaryMeta: "Internal",
    tertiaryMeta: "Testing paused",
    owner: "Infrastructure",
    updatedAt: "2026-07-05",
    href: "/feature-flags/flag_provider_failover",
  },
];

export const featureFlagsConfig: AdminModuleConfig = {
  moduleLabel: "Release controls",
  listTitle: "Feature Flags",
  listDescription:
    "Enable, disable and gradually roll out beta features across the IdentityCore platform.",
  detailBreadcrumbLabel: "Feature Flags",
  searchPlaceholder: "Search feature flags...",
  createLabel: "Create flag",
  exportLabel: "Export flags",
  filters: ["Status", "Rollout", "Owner"],
  records: featureFlagRecords,
  getRecord: (id) => featureFlagRecords.find((record) => record.id === id),
  getMetrics: (record) => [
    { label: "Rollout", value: record.primaryMeta, helper: "percentage" },
    { label: "Channel", value: record.secondaryMeta, helper: "release track" },
    { label: "Audience", value: record.tertiaryMeta, helper: "target" },
    { label: "Owner", value: record.owner, helper: "team" },
  ],
  getSections: (record) => [
    {
      title: "Rollout configuration",
      description: "Current rollout behavior and targeting rules.",
      items: [
        { label: "Status", value: record.status },
        { label: "Rollout", value: record.primaryMeta },
        { label: "Audience", value: record.tertiaryMeta },
        { label: "Rollback", value: "One-click rollback should disable the flag and notify audit/security channels." },
      ],
    },
    {
      title: "Safety checks",
      description: "Controls required before expanding rollout.",
      items: [
        { label: "Monitoring", value: "Track errors, latency, user impact and support tickets after rollout changes." },
        { label: "Approval", value: "Production rollout above 50% requires product and engineering approval." },
      ],
    },
  ],
};