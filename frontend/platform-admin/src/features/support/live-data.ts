"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type SupportTicket = {
  id: string;
  organizationId: string | null;
  organizationName: string;
  title: string;
  summary: string;
  status: string;
  priority: string;
  ownerTeam: string;
  issueType: string;
  requesterEmail: string;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

type SupportResponse = {
  platformSupportTickets: SupportTicket[];
  platformSupportTicket: SupportTicket | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "open") return "warning";
  if (status === "in progress") return "info";
  if (status === "resolved" || status === "closed") return "success";
  return "neutral";
}

export function supportRecordToAdminRecord(ticket: SupportTicket): AdminRecord {
  return {
    id: ticket.id,
    title: ticket.title,
    subtitle: ticket.summary,
    status: ticket.status,
    statusTone: tone(ticket.status.toLowerCase()),
    primaryMeta: ticket.priority,
    secondaryMeta: ticket.organizationName || "Platform",
    tertiaryMeta: ticket.issueType,
    owner: ticket.ownerTeam,
    updatedAt: formatDateTime(ticket.updatedAt),
    href: `/support/${ticket.id}`,
  };
}

export async function fetchSupportRecords() {
  const data = await graphqlRequest<SupportResponse>(
    `
      query PlatformSupportTickets($page: Int!, $pageSize: Int!) {
        platformSupportTickets(page: $page, pageSize: $pageSize) {
          id
          organizationId
          organizationName
          title
          summary
          status
          priority
          ownerTeam
          issueType
          requesterEmail
          metadata
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformSupportTickets.map(supportRecordToAdminRecord);
}

export async function fetchSupportRecord(ticketId: string) {
  const data = await graphqlRequest<SupportResponse>(
    `
      query PlatformSupportTicket($ticketId: String!) {
        platformSupportTicket(ticketId: $ticketId) {
          id
          organizationId
          organizationName
          title
          summary
          status
          priority
          ownerTeam
          issueType
          requesterEmail
          metadata
          createdAt
          updatedAt
        }
      }
    `,
    { ticketId },
  );
  return data.platformSupportTicket;
}

export function buildSupportConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Support operations",
    listTitle: "Support",
    listDescription:
      "Manage support tickets, organizations, verification lookup and controlled organization impersonation.",
    detailBreadcrumbLabel: "Support",
    searchPlaceholder: "Search tickets...",
    createLabel: "Create ticket",
    exportLabel: "Export tickets",
    filters: ["Status", "Priority", "Organization"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Priority", value: record.primaryMeta, helper: "support priority" },
      { label: "Organization", value: record.secondaryMeta, helper: "customer" },
      { label: "Area", value: record.tertiaryMeta, helper: "issue type" },
      { label: "Owner", value: record.owner, helper: "assigned team" },
    ],
    getSections: (record): AdminDetailSection[] => [
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
          {
            label: "Verification lookup",
            value:
              "Search by verification ID, organization, applicant reference or webhook event.",
          },
          {
            label: "Impersonation",
            value:
              "Requires reason, time limit and audit logging before opening organization workspace.",
          },
        ],
      },
    ],
  };
}
