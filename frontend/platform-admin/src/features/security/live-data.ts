"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type SecurityCase = {
  id: string;
  title: string;
  summary: string;
  status: string;
  severity: string;
  ownerTeam: string;
  signal: string;
  affectedSurface: string;
  detectedAt: string;
  resolvedAt: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

type SecurityResponse = {
  platformSecurityCases: SecurityCase[];
  platformSecurityCase: SecurityCase | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "blocked" || status === "critical") return "danger";
  if (status === "investigating" || status === "watching") return "warning";
  if (status === "contained" || status === "resolved") return "success";
  return "info";
}

export function securityRecordToAdminRecord(caseItem: SecurityCase): AdminRecord {
  return {
    id: caseItem.id,
    title: caseItem.title,
    subtitle: caseItem.summary,
    status: caseItem.status,
    statusTone: tone(caseItem.status.toLowerCase()),
    primaryMeta: caseItem.severity,
    secondaryMeta: caseItem.ownerTeam,
    tertiaryMeta: caseItem.affectedSurface,
    owner: caseItem.ownerTeam,
    updatedAt: formatDateTime(caseItem.updatedAt),
    href: `/security/${caseItem.id}`,
  };
}

export async function fetchSecurityRecords() {
  const data = await graphqlRequest<SecurityResponse>(
    `
      query PlatformSecurityCases($page: Int!, $pageSize: Int!) {
        platformSecurityCases(page: $page, pageSize: $pageSize) {
          id
          title
          summary
          status
          severity
          ownerTeam
          signal
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
  return data.platformSecurityCases.map(securityRecordToAdminRecord);
}

export async function fetchSecurityRecord(securityId: string) {
  const data = await graphqlRequest<SecurityResponse>(
    `
      query PlatformSecurityCase($securityId: String!) {
        platformSecurityCase(securityId: $securityId) {
          id
          title
          summary
          status
          severity
          ownerTeam
          signal
          affectedSurface
          detectedAt
          resolvedAt
          metadata
          createdAt
          updatedAt
        }
      }
    `,
    { securityId },
  );
  return data.platformSecurityCase;
}

export function buildSecurityConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Security operations",
    listTitle: "Security",
    listDescription:
      "Monitor threat detection, suspicious logins, blocked IPs, API abuse and rate limiting.",
    detailBreadcrumbLabel: "Security",
    searchPlaceholder: "Search security events...",
    createLabel: "Create rule",
    exportLabel: "Export events",
    filters: ["Risk", "Status", "Area"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Risk", value: record.primaryMeta, helper: "severity" },
      { label: "Area", value: record.secondaryMeta, helper: "surface" },
      { label: "Signal", value: record.tertiaryMeta, helper: "indicator" },
      { label: "Owner", value: record.owner, helper: "response" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Threat details",
        description: "Detection context, affected system and current response.",
        items: [
          { label: "Summary", value: record.subtitle },
          { label: "Status", value: record.status },
          { label: "Signal", value: record.tertiaryMeta },
          {
            label: "Detection",
            value: "Detected by platform security rules and anomaly scoring.",
          },
        ],
      },
      {
        title: "Controls",
        description: "Security controls applied or available.",
        items: [
          {
            label: "Rate limiting",
            value:
              "Adaptive rate limiting can be applied per organization, endpoint, token or IP.",
          },
          {
            label: "Blocking",
            value:
              "Blocked IPs and suspicious sessions are added to the platform security audit trail.",
          },
        ],
      },
    ],
  };
}
