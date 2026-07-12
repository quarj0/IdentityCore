import { restRequest } from "@/lib/admin-api";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type WebhookEndpoint = {
  id: string;
  project_id: string | null;
  url: string;
  description: string;
  events: string[];
  status: string;
  created_at: string;
  updated_at: string;
};

function formatDate(value: string) {
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
  if (status === "failed") return "danger";
  return "info";
}

export function webhookEndpointToRecord(endpoint: WebhookEndpoint): AdminRecord {
  return {
    id: endpoint.id,
    title: endpoint.url,
    subtitle: endpoint.description || "Webhook endpoint",
    status: endpoint.status,
    statusTone: tone(endpoint.status),
    primaryMeta: `${endpoint.events.length} events`,
    secondaryMeta: endpoint.project_id ?? "workspace-level",
    tertiaryMeta: `Created ${formatDate(endpoint.created_at)}`,
    owner: endpoint.project_id ?? "Platform admin",
    updatedAt: formatDate(endpoint.updated_at),
    href: `/webhooks/${endpoint.id}`,
  };
}

export async function fetchWebhookRecords() {
  const data = await restRequest<{ results: WebhookEndpoint[] }>("/platform-admin/webhooks/");
  return data.results.map(webhookEndpointToRecord);
}

export async function fetchWebhookRecord(webhookId: string) {
  return restRequest<WebhookEndpoint>(`/platform-admin/webhooks/${webhookId}`);
}

export function buildWebhookConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Webhooks",
    listTitle: "Webhooks",
    listDescription:
      "Inspect delivery endpoints, event subscriptions and webhook lifecycle state.",
    detailBreadcrumbLabel: "Webhooks",
    searchPlaceholder: "Search webhooks...",
    createLabel: "Create webhook",
    exportLabel: "Export webhooks",
    filters: ["Status", "Events", "Project"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Events", value: record.primaryMeta, helper: "subscriptions" },
      { label: "Project", value: record.secondaryMeta, helper: "scope" },
      { label: "Created", value: record.tertiaryMeta, helper: "backend" },
      { label: "Updated", value: record.updatedAt, helper: "backend" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Endpoint record",
        description: "Live webhook endpoint configuration from the backend.",
        items: [
          { label: "URL", value: record.title },
          { label: "Description", value: record.subtitle },
          { label: "Status", value: record.status },
        ],
      },
    ],
  };
}
