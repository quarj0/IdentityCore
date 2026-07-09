import type { AdminModuleConfig, AdminRecord } from "@/components/admin-module/admin-module-types";

export const supportRecords: AdminRecord[] = [
  {
    id: "ticket_1842",
    title: "Webhook verification result missing",
    subtitle: "Ghana FinTrust Bank reports delayed webhook response for completed verification.",
    status: "Open",
    statusTone: "warning",
    primaryMeta: "High priority",
    secondaryMeta: "Ghana FinTrust Bank",
    tertiaryMeta: "Webhook",
    owner: "Support Lead",
    updatedAt: "2026-07-09",
    href: "/support/ticket_1842",
  },
  {
    id: "ticket_1843",
    title: "Organization onboarding stuck",
    subtitle: "Civic Registry Authority cannot complete admin approval step.",
    status: "In progress",
    statusTone: "info",
    primaryMeta: "Medium priority",
    secondaryMeta: "Civic Registry Authority",
    tertiaryMeta: "Onboarding",
    owner: "Platform Ops",
    updatedAt: "2026-07-09",
    href: "/support/ticket_1843",
  },
  {
    id: "ticket_1844",
    title: "Verification lookup request",
    subtitle: "Support needs to inspect a verification status across provider events.",
    status: "Resolved",
    statusTone: "success",
    primaryMeta: "Low priority",
    secondaryMeta: "LagosPay",
    tertiaryMeta: "Verification lookup",
    owner: "Support Team",
    updatedAt: "2026-07-08",
    href: "/support/ticket_1844",
  },
];

export const supportConfig: AdminModuleConfig = {
  moduleLabel: "Support operations",
  listTitle: "Support",
  listDescription:
    "Manage support tickets, organizations, verification lookup and controlled organization impersonation.",
  detailBreadcrumbLabel: "Support",
  searchPlaceholder: "Search tickets...",
  createLabel: "Create ticket",
  exportLabel: "Export tickets",
  filters: ["Status", "Priority", "Organization"],
  records: supportRecords,
  getRecord: (id) => supportRecords.find((record) => record.id === id),
  getMetrics: (record) => [
    { label: "Priority", value: record.primaryMeta, helper: "support priority" },
    { label: "Organization", value: record.secondaryMeta, helper: "customer" },
    { label: "Area", value: record.tertiaryMeta, helper: "issue type" },
    { label: "Owner", value: record.owner, helper: "assigned team" },
  ],
  getSections: (record) => [
    {
      title: "Ticket details",
      description: "Support context and operational notes.",
      items: [
        { label: "Summary", value: record.subtitle },
        { label: "Status", value: record.status },
        { label: "Organization", value: record.secondaryMeta },
        { label: "Issue area", value: record.tertiaryMeta },
      ],
    },
    {
      title: "Support tools",
      description: "Safe operational tools available to support.",
      items: [
        { label: "Verification lookup", value: "Search by verification ID, organization, applicant reference or webhook event." },
        { label: "Impersonation", value: "Requires reason, time limit and audit logging before opening organization workspace." },
      ],
    },
  ],
};