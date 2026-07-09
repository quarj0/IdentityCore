import type { AdminModuleConfig, AdminRecord } from "@/components/admin-module/admin-module-types";

export const analyticsRecords: AdminRecord[] = [
  {
    id: "analytics_volume",
    title: "Verification Volume",
    subtitle: "Global verification activity across organizations, countries and workflows.",
    status: "Live",
    statusTone: "success",
    primaryMeta: "482,910 verifications",
    secondaryMeta: "+18.7%",
    tertiaryMeta: "30 days",
    owner: "Data Platform",
    updatedAt: "2026-07-09",
    href: "/analytics/analytics_volume",
  },
  {
    id: "analytics_failures",
    title: "Failure Reasons",
    subtitle: "OCR failures, face mismatch, liveness failures, document quality and policy declines.",
    status: "Live",
    statusTone: "success",
    primaryMeta: "6.4% failure rate",
    secondaryMeta: "Top: OCR quality",
    tertiaryMeta: "7 days",
    owner: "Risk Team",
    updatedAt: "2026-07-09",
    href: "/analytics/analytics_failures",
  },
  {
    id: "analytics_costs",
    title: "AI Cost Analytics",
    subtitle: "AI spend across OCR, face matching, liveness and third-party providers.",
    status: "Watch",
    statusTone: "warning",
    primaryMeta: "$14,180 spend",
    secondaryMeta: "+11.2%",
    tertiaryMeta: "30 days",
    owner: "AI Platform",
    updatedAt: "2026-07-08",
    href: "/analytics/analytics_costs",
  },
];

export const analyticsConfig: AdminModuleConfig = {
  moduleLabel: "Analytics",
  listTitle: "Analytics",
  listDescription:
    "View global charts, verification volume, failure reasons, approval rate, countries, top organizations, API usage and AI costs.",
  detailBreadcrumbLabel: "Analytics",
  searchPlaceholder: "Search analytics dashboards...",
  createLabel: "Create dashboard",
  exportLabel: "Export analytics",
  filters: ["Metric", "Period", "Owner"],
  records: analyticsRecords,
  getRecord: (id) => analyticsRecords.find((record) => record.id === id),
  getMetrics: (record) => [
    { label: "Primary metric", value: record.primaryMeta, helper: "main KPI" },
    { label: "Change", value: record.secondaryMeta, helper: "trend" },
    { label: "Period", value: record.tertiaryMeta, helper: "window" },
    { label: "Owner", value: record.owner, helper: "team" },
  ],
  getSections: (record) => [
    {
      title: "Dashboard breakdown",
      description: "Production-ready analytics sections for this dashboard.",
      items: [
        { label: "Chart", value: "Time-series chart with comparison to previous period." },
        { label: "Segmentation", value: "Break down by organization, country, workflow, template and provider." },
        { label: "Export", value: "CSV and audit-friendly export for platform analysis." },
      ],
    },
    {
      title: "Insights",
      description: "Operational signals derived from this dashboard.",
      items: [
        { label: "Trend", value: record.secondaryMeta },
        { label: "Recommended action", value: "Review top changes and compare against incidents, provider health and organization usage." },
      ],
    },
  ],
};