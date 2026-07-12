import { restRequest } from "@/lib/admin-api";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type ApiClient = {
  public_id: string;
  tenant_public_id: string;
  project_id: string | null;
  name: string;
  client_id: string;
  status: string;
  scopes: string[];
  allowed_networks: string[];
  rate_limit_per_minute: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
};

function formatDate(value: string | null) {
  if (!value) return "Never";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active") return "success";
  if (status === "disabled") return "warning";
  if (status === "rotating") return "info";
  if (status === "revoked") return "danger";
  return "neutral";
}

export function apiClientToRecord(client: ApiClient): AdminRecord {
  return {
    id: client.public_id,
    title: client.name,
    subtitle: client.client_id,
    status: client.status,
    statusTone: tone(client.status),
    primaryMeta: `${client.scopes.length} scopes`,
    secondaryMeta: `${client.allowed_networks.length} networks`,
    tertiaryMeta: `Rate ${client.rate_limit_per_minute}/min`,
    owner: client.tenant_public_id,
    updatedAt: formatDate(client.updated_at),
    href: `/api-clients/${client.public_id}`,
  };
}

export async function fetchApiClientRecords() {
  const data = await restRequest<{ results: ApiClient[] }>("/platform-admin/api-clients/");
  return data.results.map(apiClientToRecord);
}

export async function fetchApiClientRecord(clientId: string) {
  return restRequest<ApiClient>(`/platform-admin/api-clients/${clientId}`);
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
