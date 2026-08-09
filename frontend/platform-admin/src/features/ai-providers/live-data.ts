"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type Provider = {
  id: string;
  name: string;
  code: string;
  providerType: string;
  status: string;
  configuration: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

type ProviderCheck = {
  id: string;
  providerId: string;
  providerCode: string;
  checkType: string;
  status: string;
  providerReference: string;
  errorCode: string;
  durationMs: number | null;
  startedAt: string;
  completedAt: string | null;
};

type ProviderHealthMetric = {
  provider_id: string;
  status: string;
  total_attempts: number;
  successful_attempts: number;
  failed_attempts: number;
  availability_percent: number;
  error_rate_percent: number;
  latency_ms: {
    p50: number | null;
    p95: number | null;
    maximum: number | null;
  };
};

type RouteHealth = {
  route_id: string;
  route_key: string;
  route_version: number;
  capability: string;
  status: string;
  steps: Array<{
    position: number;
    provider_id: string;
    provider_code: string;
    circuit_status: string;
    circuit_retry_after: string | null;
    health: string;
  }>;
};

type ProviderHealthSnapshot = {
  scope: { tenant_id: string; environment: string; window_hours: number };
  providers: ProviderHealthMetric[];
  routes: RouteHealth[];
};

type ProviderResponse = {
  platformAiProviders: Provider[];
  platformAiProvider: Provider | null;
  platformProviderChecks: ProviderCheck[];
  platformProviderHealth: ProviderHealthSnapshot[];
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active" || status === "operational") return "success";
  if (status === "testing" || status === "degraded") return "warning";
  if (status === "disabled" || status === "failed") return "danger";
  return "info";
}

function providerLabel(providerType: string) {
  return providerType.replace(/_/g, " ");
}

export function providerToAdminRecord(provider: Provider): AdminRecord {
  return {
    id: provider.id,
    title: provider.name,
    subtitle: `${providerLabel(provider.providerType)} · ${provider.code}`,
    status: provider.status,
    statusTone: tone(provider.status),
    primaryMeta: provider.providerType,
    secondaryMeta: provider.code,
    tertiaryMeta: `Config keys: ${Object.keys(provider.configuration || {}).length}`,
    owner: "AI Platform",
    updatedAt: formatDateTime(provider.updatedAt),
    href: `/ai-providers/${provider.id}`,
  };
}

export async function fetchAiProviderRecords() {
  const data = await graphqlRequest<ProviderResponse>(
    `
      query PlatformAiProviders {
        platformAiProviders {
          id
          name
          code
          providerType
          status
          configuration
          createdAt
          updatedAt
        }
      }
    `,
  );
  return data.platformAiProviders.map(providerToAdminRecord);
}

export async function fetchAiProviderRecord(providerId: string) {
  const data = await graphqlRequest<ProviderResponse>(
    `
      query PlatformAiProvider($providerId: String!) {
        platformAiProvider(providerId: $providerId) {
          id
          name
          code
          providerType
          status
          configuration
          createdAt
          updatedAt
        }
        platformProviderChecks(providerId: $providerId) {
          id
          providerId
          providerCode
          checkType
          status
          providerReference
          errorCode
          durationMs
          startedAt
          completedAt
        }
        platformProviderHealth(providerId: $providerId)
      }
    `,
    { providerId },
  );
  return {
    provider: data.platformAiProvider,
    checks: data.platformProviderChecks,
    health: data.platformProviderHealth,
  };
}

export function buildAiProviderConfig(
  records: AdminRecord[],
  checks: ProviderCheck[] = [],
  health: ProviderHealthSnapshot[] = [],
): AdminModuleConfig {
  const providerMetrics = health.flatMap((snapshot) => snapshot.providers);
  const totalAttempts = providerMetrics.reduce(
    (total, metric) => total + metric.total_attempts,
    0,
  );
  const activeRoutes = health.reduce(
    (total, snapshot) => total + snapshot.routes.length,
    0,
  );
  const visibleStatuses = [
    ...providerMetrics.map((metric) => metric.status),
    ...health.flatMap((snapshot) =>
      snapshot.routes.map((route) => route.status),
    ),
  ];
  const healthStatus = visibleStatuses.some((status) => status === "unavailable")
    ? "Unavailable"
    : visibleStatuses.some((status) => status === "degraded")
      ? "Degraded"
      : visibleStatuses.some((status) => status === "healthy")
        ? "Healthy"
        : "No data";

  return {
    moduleLabel: "AI infrastructure",
    listTitle: "AI Providers",
    listDescription:
      "Manage live AI provider registry entries used by document, biometric and liveness processing.",
    detailBreadcrumbLabel: "AI Providers",
    searchPlaceholder: "Search AI providers...",
    createLabel: "Add provider",
    exportLabel: "Export",
    filters: ["Type", "Status", "Region"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (): AdminDetailMetric[] => [
      {
        label: "Scoped status",
        value: healthStatus,
        helper: "worst visible scope",
      },
      {
        label: "Attempts",
        value: String(totalAttempts),
        helper: "displayed scopes",
      },
      {
        label: "Active routes",
        value: String(activeRoutes),
        helper: "displayed scopes",
      },
      {
        label: "Scopes",
        value: String(health.length),
        helper: "tenant environments",
      },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Provider record",
        description: "Backend provider registry details.",
        items: [
          { label: "Name", value: record.title },
          { label: "Status", value: record.status },
          { label: "Type", value: providerLabel(record.primaryMeta) },
          { label: "Updated", value: record.updatedAt },
        ],
      },
      {
        title: "Recent checks",
        description: "Latest provider checks from the backend.",
        items: checks.length
          ? checks.map((check) => ({
              label: `${check.checkType} · ${check.status}`,
              value: `${formatDateTime(check.startedAt)}${check.completedAt ? ` → ${formatDateTime(check.completedAt)}` : ""}${check.durationMs !== null ? ` · ${check.durationMs} ms` : ""}${check.errorCode ? ` · ${check.errorCode}` : ""}`,
            }))
          : [{ label: "Checks", value: "No provider checks found." }],
      },
      {
        title: "Scoped health",
        description:
          "Redacted availability, error-rate and latency metrics remain separated by tenant and environment.",
        items: health.length
          ? health.map((snapshot) => {
              const metric = snapshot.providers[0];
              return {
                label: `${snapshot.scope.tenant_id} · ${snapshot.scope.environment}`,
                value: metric
                  ? `${metric.status} · ${metric.availability_percent}% available · ${metric.error_rate_percent}% errors · p95 ${metric.latency_ms.p95 ?? "n/a"} ms`
                  : "No attempts in this window",
              };
            })
          : [{ label: "Health", value: "No scoped health data found." }],
      },
      {
        title: "Route health",
        description:
          "Current route and circuit state without credentials or provider payloads.",
        items: health.some((snapshot) => snapshot.routes.length)
          ? health.flatMap((snapshot) =>
              snapshot.routes.map((route) => ({
                label: `${snapshot.scope.tenant_id} · ${route.route_key} v${route.route_version} · ${snapshot.scope.environment}`,
                value: `${route.status} · ${route.capability} · ${route.steps.map((step) => `${step.position}. ${step.provider_code} (${step.circuit_status})`).join(" → ")}`,
              })),
            )
          : [{ label: "Routes", value: "No active routes found." }],
      },
      {
        title: "Configuration",
        description: "Provider configuration stored in the backend.",
        items: [
          {
            label: "Config keys",
            value: record.tertiaryMeta,
          },
        ],
      },
    ],
  };
}
