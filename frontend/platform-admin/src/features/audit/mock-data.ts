import type { AdminModuleConfig, AdminRecord } from "@/components/admin-module/admin-module-types";

export const auditRecords: AdminRecord[] = [
  {
    id: "audit_9001",
    title: "Organization suspended",
    subtitle: "HealthPass Clinics was suspended by platform administrator after compliance review.",
    status: "Completed",
    statusTone: "success",
    primaryMeta: "Organization",
    secondaryMeta: "Suspend",
    tertiaryMeta: "High impact",
    owner: "Ama Mensah",
    updatedAt: "2026-07-09 09:15",
    href: "/audit/audit_9001",
  },
  {
    id: "audit_9002",
    title: "AI provider priority changed",
    subtitle: "PaddleOCR failover priority was changed due to latency threshold.",
    status: "Completed",
    statusTone: "success",
    primaryMeta: "AI Provider",
    secondaryMeta: "Update",
    tertiaryMeta: "Medium impact",
    owner: "Tunde Adebayo",
    updatedAt: "2026-07-09 08:42",
    href: "/audit/audit_9002",
  },
  {
    id: "audit_9003",
    title: "Audit export generated",
    subtitle: "SOC2 evidence export generated for platform-wide access review.",
    status: "Exported",
    statusTone: "info",
    primaryMeta: "Compliance",
    secondaryMeta: "Export",
    tertiaryMeta: "Low impact",
    owner: "Compliance Team",
    updatedAt: "2026-07-08 16:03",
    href: "/audit/audit_9003",
  },
];

export const auditConfig: AdminModuleConfig = {
  moduleLabel: "Platform audit",
  listTitle: "Audit",
  listDescription:
    "Search, filter and export platform-wide audit events across all IdentityCore modules.",
  detailBreadcrumbLabel: "Audit",
  searchPlaceholder: "Search audit events...",
  createLabel: "Create export",
  exportLabel: "Export audit",
  filters: ["Actor", "Action", "Module"],
  records: auditRecords,
  getRecord: (id) => auditRecords.find((record) => record.id === id),
  getMetrics: (record) => [
    { label: "Module", value: record.primaryMeta, helper: "area" },
    { label: "Action", value: record.secondaryMeta, helper: "operation" },
    { label: "Impact", value: record.tertiaryMeta, helper: "risk" },
    { label: "Actor", value: record.owner, helper: "performed by" },
  ],
  getSections: (record) => [
    {
      title: "Audit event",
      description: "Immutable event details for this platform action.",
      items: [
        { label: "Event", value: record.title },
        { label: "Description", value: record.subtitle },
        { label: "Actor", value: record.owner },
        { label: "Timestamp", value: record.updatedAt },
      ],
    },
    {
      title: "Export readiness",
      description: "Audit export and compliance evidence details.",
      items: [
        { label: "Integrity", value: "Event should be immutable and signed by the audit logging service." },
        { label: "Export", value: "Available in CSV and JSON for compliance reviews." },
      ],
    },
  ],
};