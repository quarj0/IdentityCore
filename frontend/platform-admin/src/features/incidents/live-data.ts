"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type Incident = {
  id: string;
  title: string;
  summary: string;
  status: string;
  severity: string;
  ownerTeam: string;
  affectedSurface: string;
  detectedAt: string;
  resolvedAt: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

type IncidentResponse = {
  platformIncidents: Incident[];
  platformIncident: Incident | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "investigating" || status === "monitoring") return "warning";
  if (status === "resolved" || status === "contained") return "success";
  if (status === "scheduled") return "info";
  return "neutral";
}

export function incidentRecordToAdminRecord(incident: Incident): AdminRecord {
  return {
    id: incident.id,
    title: incident.title,
    subtitle: incident.summary,
    status: incident.status,
    statusTone: tone(incident.status.toLowerCase()),
    primaryMeta: incident.severity,
    secondaryMeta: incident.ownerTeam,
    tertiaryMeta: incident.affectedSurface,
    owner: incident.ownerTeam,
    updatedAt: formatDateTime(incident.updatedAt),
    href: `/incidents/${incident.id}`,
  };
}

export async function fetchIncidentRecords() {
  const data = await graphqlRequest<IncidentResponse>(
    `
      query PlatformIncidents($page: Int!, $pageSize: Int!) {
        platformIncidents(page: $page, pageSize: $pageSize) {
          id
          title
          summary
          status
          severity
          ownerTeam
          affectedSurface
          detectedAt
          resolvedAt
          metadata
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformIncidents.map(incidentRecordToAdminRecord);
}

export async function fetchIncidentRecord(incidentId: string) {
  const data = await graphqlRequest<IncidentResponse>(
    `
      query PlatformIncident($incidentId: String!) {
        platformIncident(incidentId: $incidentId) {
          id
          title
          summary
          status
          severity
          ownerTeam
          affectedSurface
          detectedAt
          resolvedAt
          metadata
          createdAt
          updatedAt
        }
      }
    `,
    { incidentId },
  );
  return data.platformIncident;
}

export function buildIncidentConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Platform reliability",
    listTitle: "Incidents",
    listDescription:
      "Manage status page updates, outages, maintenance windows and incident history.",
    detailBreadcrumbLabel: "Incidents",
    searchPlaceholder: "Search incidents...",
    createLabel: "Create incident",
    exportLabel: "Export history",
    filters: ["Severity", "Status", "Service"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Severity", value: record.primaryMeta, helper: "impact" },
      { label: "Region", value: record.secondaryMeta, helper: "scope" },
      { label: "Service", value: record.tertiaryMeta, helper: "component" },
      { label: "Owner", value: record.owner, helper: "responder" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Incident timeline",
        description: "Current operational timeline for this incident.",
        items: [
          {
            label: "Detected",
            value:
              "Alert triggered by provider health and latency monitors.",
          },
          { label: "Current status", value: record.status },
          {
            label: "Customer impact",
            value:
              "Verification completion may be delayed but failover keeps core workflow available.",
          },
          {
            label: "Next update",
            value: "Post update to status page every 30 minutes until resolved.",
          },
        ],
      },
      {
        title: "Response plan",
        description: "Operational response and recovery steps.",
        items: [
          {
            label: "Mitigation",
            value: "Enable failover, scale workers and monitor queue depth.",
          },
          { label: "Postmortem", value: "Required for major and critical incidents." },
        ],
      },
    ],
  };
}
