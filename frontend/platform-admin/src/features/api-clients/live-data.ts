"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type ApiClient = {
  publicId: string;
  tenantPublicId: string;
  projectId: string | null;
  name: string;
  clientId: string;
  status: string;
  scopes: string[];
  allowedNetworks: string[];
  rateLimitPerMinute: number;
  lastUsedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

type ApiClientResponse = {
  platformApiClients: ApiClient[];
  platformApiClient: ApiClient | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active") return "success";
  if (status === "disabled") return "warning";
  if (status === "rotating") return "info";
  if (status === "revoked") return "danger";
  return "neutral";
}

export function apiClientRecordToAdminRecord(client: ApiClient): AdminRecord {
  return {
    id: client.publicId,
    title: client.name,
    subtitle: client.clientId,
    status: client.status,
    statusTone: tone(client.status.toLowerCase()),
    primaryMeta: `${client.scopes.length} scopes`,
    secondaryMeta: `${client.allowedNetworks.length} networks`,
    tertiaryMeta: `Rate ${client.rateLimitPerMinute}/min`,
    owner: client.tenantPublicId,
    updatedAt: formatDateTime(client.updatedAt),
    href: `/api-clients/${client.publicId}`,
  };
}

export async function fetchApiClientRecords() {
  const data = await graphqlRequest<ApiClientResponse>(
    `
      query PlatformApiClients($page: Int!, $pageSize: Int!) {
        platformApiClients(page: $page, pageSize: $pageSize) {
          publicId
          tenantPublicId
          projectId
          name
          clientId
          status
          scopes
          allowedNetworks
          rateLimitPerMinute
          lastUsedAt
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformApiClients.map(apiClientRecordToAdminRecord);
}

export async function fetchApiClientRecord(clientId: string) {
  const data = await graphqlRequest<ApiClientResponse>(
    `
      query PlatformApiClient($clientId: String!) {
        platformApiClient(clientId: $clientId) {
          publicId
          tenantPublicId
          projectId
          name
          clientId
          status
          scopes
          allowedNetworks
          rateLimitPerMinute
          lastUsedAt
          createdAt
          updatedAt
        }
      }
    `,
    { clientId },
  );
  return data.platformApiClient;
}

export function buildApiClientConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "API clients",
    listTitle: "API Clients",
    listDescription:
      "Review service integrations, scopes, IP allowlists and client lifecycle state.",
    detailBreadcrumbLabel: "API Clients",
    searchPlaceholder: "Search API clients...",
    createLabel: "Create client",
    exportLabel: "Export clients",
    filters: ["Status", "Scopes", "Project"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Scopes", value: record.primaryMeta, helper: "permissions" },
      { label: "Allowlist", value: record.secondaryMeta, helper: "network rules" },
      { label: "Rate limit", value: record.tertiaryMeta, helper: "requests" },
      { label: "Tenant", value: record.owner, helper: "owner" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Client record",
        description: "Live client configuration from the backend.",
        items: [
          { label: "Client ID", value: record.subtitle },
          { label: "Status", value: record.status },
          { label: "Last updated", value: record.updatedAt },
        ],
      },
    ],
  };
}
