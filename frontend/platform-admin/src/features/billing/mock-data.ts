import type { AdminModuleConfig, AdminRecord } from "@/components/admin-module/admin-module-types";

export const billingRecords: AdminRecord[] = [
  {
    id: "bill_fintrust",
    title: "Ghana FinTrust Bank",
    subtitle: "Enterprise subscription with usage-based verification billing.",
    status: "Paid",
    statusTone: "success",
    primaryMeta: "$12,840 MRR",
    secondaryMeta: "482,100 checks",
    tertiaryMeta: "Invoice INV-1048",
    owner: "Billing Team",
    updatedAt: "2026-07-09",
    href: "/billing/bill_fintrust",
  },
  {
    id: "bill_lagospay",
    title: "LagosPay",
    subtitle: "Growth subscription with increased OCR and liveness usage.",
    status: "Due soon",
    statusTone: "warning",
    primaryMeta: "$8,210 MRR",
    secondaryMeta: "314,900 checks",
    tertiaryMeta: "Invoice INV-1049",
    owner: "Billing Team",
    updatedAt: "2026-07-08",
    href: "/billing/bill_lagospay",
  },
  {
    id: "bill_healthpass",
    title: "HealthPass Clinics",
    subtitle: "Suspended organization with unpaid invoice and reduced usage.",
    status: "Overdue",
    statusTone: "danger",
    primaryMeta: "$620 MRR",
    secondaryMeta: "12,900 checks",
    tertiaryMeta: "$1,840 overdue",
    owner: "Finance Ops",
    updatedAt: "2026-07-04",
    href: "/billing/bill_healthpass",
  },
];

export const billingConfig: AdminModuleConfig = {
  moduleLabel: "Billing",
  listTitle: "Billing",
  listDescription:
    "Manage organizations, invoices, subscriptions, usage, revenue and platform fees.",
  detailBreadcrumbLabel: "Billing",
  searchPlaceholder: "Search billing records...",
  createLabel: "Create invoice",
  exportLabel: "Export revenue",
  filters: ["Status", "Plan", "Invoice"],
  records: billingRecords,
  getRecord: (id) => billingRecords.find((record) => record.id === id),
  getMetrics: (record) => [
    { label: "MRR", value: record.primaryMeta, helper: "monthly revenue" },
    { label: "Usage", value: record.secondaryMeta, helper: "monthly checks" },
    { label: "Invoice", value: record.tertiaryMeta, helper: "current cycle" },
    { label: "Owner", value: record.owner, helper: "billing owner" },
  ],
  getSections: (record) => [
    {
      title: "Subscription",
      description: "Plan, billing status and commercial summary.",
      items: [
        { label: "Current status", value: record.status },
        { label: "Monthly recurring revenue", value: record.primaryMeta },
        { label: "Usage volume", value: record.secondaryMeta },
        { label: "Current invoice", value: record.tertiaryMeta },
      ],
    },
    {
      title: "Usage billing",
      description: "Usage-based billing breakdown.",
      items: [
        { label: "Verification checks", value: "Document OCR, face match, liveness and manual review billable events." },
        { label: "Platform fees", value: "Applied according to organization plan and volume tier." },
      ],
    },
  ],
};