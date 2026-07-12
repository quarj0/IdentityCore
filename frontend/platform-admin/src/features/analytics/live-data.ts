"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type AnalyticsDashboard = {
  id: string;
  code: string;
  title: string;
  description: string;
  status: string;
  primaryMetric: string;
  secondaryMetric: string;
  tertiaryMetric: string;
  timeWindow: string;
  ownerTeam: string;
  config: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

type AnalyticsResponse = {
  platformAnalyticsDashboards: AnalyticsDashboard[];
  platformAnalyticsDashboard: AnalyticsDashboard | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "live" || status === "enabled" || status === "active") return "success";
  if (status === "watch" || status === "draft") return "warning";
  if (status === "disabled" || status === "archived") return "neutral";
  return "info";
}

export function analyticsRecordToAdminRecord(dashboard: AnalyticsDashboard): AdminRecord {
  return {
    id: dashboard.id,
    title: dashboard.title,
    subtitle: dashboard.description,
    status: dashboard.status,
    statusTone: tone(dashboard.status.toLowerCase()),
    primaryMeta: dashboard.primaryMetric,
    secondaryMeta: dashboard.secondaryMetric,
    tertiaryMeta: dashboard.timeWindow,
    owner: dashboard.ownerTeam,
    updatedAt: formatDateTime(dashboard.updatedAt),
    href: `/analytics/${dashboard.id}`,
  };
}

export async function fetchAnalyticsRecords() {
  const data = await graphqlRequest<AnalyticsResponse>(
    `
      query PlatformAnalyticsDashboards($page: Int!, $pageSize: Int!) {
        platformAnalyticsDashboards(page: $page, pageSize: $pageSize) {
          id
          code
          title
          description
          status
          primaryMetric
          secondaryMetric
          tertiaryMetric
          timeWindow
          ownerTeam
          config
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformAnalyticsDashboards.map(analyticsRecordToAdminRecord);
}

export async function fetchAnalyticsRecord(dashboardId: string) {
  const data = await graphqlRequest<AnalyticsResponse>(
    `
      query PlatformAnalyticsDashboard($dashboardId: String!) {
        platformAnalyticsDashboard(dashboardId: $dashboardId) {
          id
          code
          title
          description
          status
          primaryMetric
          secondaryMetric
          tertiaryMetric
          timeWindow
          ownerTeam
          config
          createdAt
          updatedAt
        }
      }
    `,
    { dashboardId },
  );
  return data.platformAnalyticsDashboard;
}

export function buildAnalyticsConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Analytics",
    listTitle: "Analytics",
    listDescription:
      "View global charts, verification volume, failure reasons, approval rate, countries, top organizations, API usage and AI costs.",
    detailBreadcrumbLabel: "Analytics",
    searchPlaceholder: "Search analytics dashboards...",
    createLabel: "Create dashboard",
    exportLabel: "Export analytics",
    filters: ["Metric", "Period", "Owner"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Primary metric", value: record.primaryMeta, helper: "main KPI" },
      { label: "Change", value: record.secondaryMeta, helper: "trend" },
      { label: "Period", value: record.tertiaryMeta, helper: "window" },
      { label: "Owner", value: record.owner, helper: "team" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Dashboard breakdown",
        description: "Production-ready analytics sections for this dashboard.",
        items: [
          {
            label: "Chart",
            value: "Time-series chart with comparison to previous period.",
          },
          {
            label: "Segmentation",
            value:
              "Break down by organization, country, workflow, template and provider.",
          },
          {
            label: "Export",
            value: "CSV and audit-friendly export for platform analysis.",
          },
        ],
      },
      {
        title: "Insights",
        description: "Operational signals derived from this dashboard.",
        items: [
          { label: "Trend", value: record.secondaryMeta },
          {
            label: "Recommended action",
            value:
              "Review top changes and compare against incidents, provider health and organization usage.",
          },
        ],
      },
    ],
  };
}
