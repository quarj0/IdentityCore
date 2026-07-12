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
  errorMessage: string;
  startedAt: string;
  completedAt: string | null;
};

type ProviderResponse = {
  platformAiProviders: Provider[];
  platformAiProvider: Provider | null;
  platformProviderChecks: ProviderCheck[];
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
          errorMessage
          startedAt
          completedAt
        }
      }
    `,
    { providerId },
  );
  return {
    provider: data.platformAiProvider,
    checks: data.platformProviderChecks,
  };
}

export function buildAiProviderConfig(
  records: AdminRecord[],
  checks: ProviderCheck[] = [],
): AdminModuleConfig {
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
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Type", value: record.primaryMeta, helper: "provider class" },
      { label: "Code", value: record.secondaryMeta, helper: "registry code" },
      { label: "Config", value: record.tertiaryMeta, helper: "backend" },
      { label: "Updated", value: record.updatedAt, helper: "backend" },
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
              value: `${formatDateTime(check.startedAt)}${check.completedAt ? ` → ${formatDateTime(check.completedAt)}` : ""}${check.errorMessage ? ` · ${check.errorMessage}` : ""}`,
            }))
          : [{ label: "Checks", value: "No provider checks found." }],
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
