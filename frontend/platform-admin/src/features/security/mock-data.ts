import type { AdminModuleConfig, AdminRecord } from "@/components/admin-module/admin-module-types";

export const securityRecords: AdminRecord[] = [
  {
    id: "sec_suspicious_login",
    title: "Suspicious admin login",
    subtitle: "Unusual location and impossible travel signal for platform admin account.",
    status: "Investigating",
    statusTone: "warning",
    primaryMeta: "High risk",
    secondaryMeta: "Admin access",
    tertiaryMeta: "Accra → London",
    owner: "Security Team",
    updatedAt: "2026-07-09",
    href: "/security/sec_suspicious_login",
  },
  {
    id: "sec_api_abuse",
    title: "API abuse detection",
    subtitle: "One organization exceeded expected request pattern for document OCR endpoint.",
    status: "Blocked",
    statusTone: "danger",
    primaryMeta: "Critical",
    secondaryMeta: "API Gateway",
    tertiaryMeta: "Rate limit active",
    owner: "Security Team",
    updatedAt: "2026-07-09",
    href: "/security/sec_api_abuse",
  },
  {
    id: "sec_blocked_ip",
    title: "Blocked IP campaign",
    subtitle: "Repeated credential stuffing attempts blocked at edge and application layers.",
    status: "Contained",
    statusTone: "success",
    primaryMeta: "Medium risk",
    secondaryMeta: "Authentication",
    tertiaryMeta: "42 IPs blocked",
    owner: "Security Team",
    updatedAt: "2026-07-08",
    href: "/security/sec_blocked_ip",
  },
];

export const securityConfig: AdminModuleConfig = {
  moduleLabel: "Security operations",
  listTitle: "Security",
  listDescription:
    "Monitor threat detection, suspicious logins, blocked IPs, API abuse and rate limiting.",
  detailBreadcrumbLabel: "Security",
  searchPlaceholder: "Search security events...",
  createLabel: "Create rule",
  exportLabel: "Export events",
  filters: ["Risk", "Status", "Area"],
  records: securityRecords,
  getRecord: (id) => securityRecords.find((record) => record.id === id),
  getMetrics: (record) => [
    { label: "Risk", value: record.primaryMeta, helper: "severity" },
    { label: "Area", value: record.secondaryMeta, helper: "surface" },
    { label: "Signal", value: record.tertiaryMeta, helper: "indicator" },
    { label: "Owner", value: record.owner, helper: "response" },
  ],
  getSections: (record) => [
    {
      title: "Threat details",
      description: "Detection context, affected system and current response.",
      items: [
        { label: "Summary", value: record.subtitle },
        { label: "Status", value: record.status },
        { label: "Signal", value: record.tertiaryMeta },
        { label: "Detection", value: "Detected by platform security rules and anomaly scoring." },
      ],
    },
    {
      title: "Controls",
      description: "Security controls applied or available.",
      items: [
        { label: "Rate limiting", value: "Adaptive rate limiting can be applied per organization, endpoint, token or IP." },
        { label: "Blocking", value: "Blocked IPs and suspicious sessions are added to the platform security audit trail." },
      ],
    },
  ],
};