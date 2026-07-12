"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type WebhookEndpoint = {
  id: string;
  projectId: string | null;
  url: string;
  description: string;
  events: string[];
  status: string;
  createdAt: string;
  updatedAt: string;
};

type WebhookResponse = {
  platformWebhookEndpoints: WebhookEndpoint[];
  platformWebhookEndpoint: WebhookEndpoint | null;
};

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
    statusTone: tone(endpoint.status.toLowerCase()),
    primaryMeta: `${endpoint.events.length} events`,
    secondaryMeta: endpoint.projectId ?? "workspace-level",
    tertiaryMeta: `Created ${formatDateTime(endpoint.createdAt)}`,
    owner: endpoint.projectId ?? "Platform admin",
    updatedAt: formatDateTime(endpoint.updatedAt),
    href: `/webhooks/${endpoint.id}`,
  };
}

export async function fetchWebhookRecords() {
  const data = await graphqlRequest<WebhookResponse>(
    `
      query PlatformWebhookEndpoints($page: Int!, $pageSize: Int!) {
        platformWebhookEndpoints(page: $page, pageSize: $pageSize) {
          id
          projectId
          url
          description
          events
          status
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformWebhookEndpoints.map(webhookEndpointToRecord);
}

export async function fetchWebhookRecord(webhookId: string) {
  const data = await graphqlRequest<WebhookResponse>(
    `
      query PlatformWebhookEndpoint($webhookId: String!) {
        platformWebhookEndpoint(webhookId: $webhookId) {
          id
          projectId
          url
          description
          events
          status
          createdAt
          updatedAt
        }
      }
    `,
    { webhookId },
  );
  return data.platformWebhookEndpoint;
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
