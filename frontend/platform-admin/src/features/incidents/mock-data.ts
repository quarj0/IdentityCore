import type { AdminModuleConfig, AdminRecord } from "@/components/admin-module/admin-module-types";

export const incidentRecords: AdminRecord[] = [
  {
    id: "inc_ocr_latency",
    title: "OCR latency elevated in Africa West",
    subtitle: "PaddleOCR workers are processing slower than expected. Failover is active.",
    status: "Investigating",
    statusTone: "warning",
    primaryMeta: "Major",
    secondaryMeta: "Africa West",
    tertiaryMeta: "OCR service",
    owner: "AI Platform",
    updatedAt: "2026-07-09",
    href: "/incidents/inc_ocr_latency",
  },
  {
    id: "inc_webhook_retries",
    title: "Webhook retries increased",
    subtitle: "Some organizations are receiving delayed webhook delivery under retry policy.",
    status: "Monitoring",
    statusTone: "info",
    primaryMeta: "Minor",
    secondaryMeta: "Global",
    tertiaryMeta: "Webhook delivery",
    owner: "Infrastructure",
    updatedAt: "2026-07-09",
    href: "/incidents/inc_webhook_retries",
  },
  {
    id: "inc_storage_maintenance",
    title: "Evidence storage maintenance",
    subtitle: "Scheduled maintenance for evidence storage lifecycle processing.",
    status: "Scheduled",
    statusTone: "neutral",
    primaryMeta: "Maintenance",
    secondaryMeta: "Multi-region",
    tertiaryMeta: "Storage",
    owner: "Platform Ops",
    updatedAt: "2026-07-08",
    href: "/incidents/inc_storage_maintenance",
  },
];

export const incidentsConfig: AdminModuleConfig = {
  moduleLabel: "Platform reliability",
  listTitle: "Incidents",
  listDescription:
    "Manage status page updates, outages, maintenance windows and incident history.",
  detailBreadcrumbLabel: "Incidents",
  searchPlaceholder: "Search incidents...",
  createLabel: "Create incident",
  exportLabel: "Export history",
  filters: ["Severity", "Status", "Service"],
  records: incidentRecords,
  getRecord: (id) => incidentRecords.find((record) => record.id === id),
  getMetrics: (record) => [
    { label: "Severity", value: record.primaryMeta, helper: "impact" },
    { label: "Region", value: record.secondaryMeta, helper: "scope" },
    { label: "Service", value: record.tertiaryMeta, helper: "component" },
    { label: "Owner", value: record.owner, helper: "responder" },
  ],
  getSections: (record) => [
    {
      title: "Incident timeline",
      description: "Current operational timeline for this incident.",
      items: [
        { label: "Detected", value: "Alert triggered by provider health and latency monitors." },
        { label: "Current status", value: record.status },
        { label: "Customer impact", value: "Verification completion may be delayed but failover keeps core workflow available." },
        { label: "Next update", value: "Post update to status page every 30 minutes until resolved." },
      ],
    },
    {
      title: "Response plan",
      description: "Operational response and recovery steps.",
      items: [
        { label: "Mitigation", value: "Enable failover, scale workers and monitor queue depth." },
        { label: "Postmortem", value: "Required for major and critical incidents." },
      ],
    },
  ],
};