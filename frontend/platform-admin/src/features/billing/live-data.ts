"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type BillingRecord = {
  id: string;
  title: string;
  subtitle: string;
  status: string;
  monthlyRecurringRevenue: string;
  monthlyCheckCount: number;
  currentInvoice: string;
  plan: string;
  billingCycle: string;
  ownerTeam: string;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

type BillingResponse = {
  platformBillingRecords: BillingRecord[];
  platformBillingRecord: BillingRecord | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "paid") return "success";
  if (status === "due soon" || status === "trialing") return "warning";
  if (status === "overdue" || status === "suspended") return "danger";
  return "info";
}

export function billingRecordToAdminRecord(record: BillingRecord): AdminRecord {
  return {
    id: record.id,
    title: record.title,
    subtitle: record.subtitle || `${record.plan} subscription`,
    status: record.status,
    statusTone: tone(record.status.toLowerCase()),
    primaryMeta: record.monthlyRecurringRevenue,
    secondaryMeta: `${record.monthlyCheckCount.toLocaleString()} checks`,
    tertiaryMeta: record.currentInvoice,
    owner: record.ownerTeam,
    updatedAt: formatDateTime(record.updatedAt),
    href: `/billing/${record.id}`,
  };
}

export async function fetchBillingRecords() {
  const data = await graphqlRequest<BillingResponse>(
    `
      query PlatformBillingRecords($page: Int!, $pageSize: Int!) {
        platformBillingRecords(page: $page, pageSize: $pageSize) {
          id
          title
          subtitle
          status
          monthlyRecurringRevenue
          monthlyCheckCount
          currentInvoice
          plan
          billingCycle
          ownerTeam
          notes
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );

  return data.platformBillingRecords.map(billingRecordToAdminRecord);
}

export async function fetchBillingRecord(billingId: string) {
  const data = await graphqlRequest<BillingResponse>(
    `
      query PlatformBillingRecord($billingId: String!) {
        platformBillingRecord(billingId: $billingId) {
          id
          title
          subtitle
          status
          monthlyRecurringRevenue
          monthlyCheckCount
          currentInvoice
          plan
          billingCycle
          ownerTeam
          notes
          createdAt
          updatedAt
        }
      }
    `,
    { billingId },
  );

  return data.platformBillingRecord;
}

export function buildBillingConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Billing",
    listTitle: "Billing",
    listDescription:
      "Manage organizations, invoices, subscriptions, usage, revenue and platform fees.",
    detailBreadcrumbLabel: "Billing",
    searchPlaceholder: "Search billing records...",
    createLabel: "Create invoice",
    exportLabel: "Export revenue",
    filters: ["Status", "Plan", "Invoice"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "MRR", value: record.primaryMeta, helper: "monthly revenue" },
      { label: "Usage", value: record.secondaryMeta, helper: "monthly checks" },
      { label: "Invoice", value: record.tertiaryMeta, helper: "current cycle" },
      { label: "Owner", value: record.owner, helper: "billing owner" },
    ],
    getSections: (record): AdminDetailSection[] => [
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
          {
            label: "Verification checks",
            value:
              "Document OCR, face match, liveness and manual review billable events.",
          },
          {
            label: "Platform fees",
            value: "Applied according to organization plan and volume tier.",
          },
        ],
      },
    ],
  };
}
