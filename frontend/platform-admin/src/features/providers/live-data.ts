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

type ProviderResponse = {
  platformProviders: Provider[];
  platformProvider: Provider | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active" || status === "operational") return "success";
  if (status === "testing" || status === "degraded") return "warning";
  if (status === "disabled" || status === "failed") return "danger";
  return "info";
}

export function providerRecordToAdminRecord(provider: Provider): AdminRecord {
  return {
    id: provider.id,
    title: provider.name,
    subtitle: `${provider.providerType.replace(/_/g, " ")} · ${provider.code}`,
    status: provider.status,
    statusTone: tone(provider.status.toLowerCase()),
    primaryMeta: provider.providerType,
    secondaryMeta: provider.code,
    tertiaryMeta: `Config keys: ${Object.keys(provider.configuration || {}).length}`,
    owner: "Platform admin",
    updatedAt: formatDateTime(provider.updatedAt),
    href: `/providers/${provider.id}`,
  };
}

export async function fetchVerificationProviderRecords() {
  const data = await graphqlRequest<ProviderResponse>(
    `
      query PlatformProviders {
        platformProviders {
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
  return data.platformProviders.map(providerRecordToAdminRecord);
}

export async function fetchVerificationProviderRecord(providerId: string) {
  const data = await graphqlRequest<ProviderResponse>(
    `
      query PlatformProvider($providerId: String!) {
        platformProvider(providerId: $providerId) {
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
    { providerId },
  );
  return data.platformProvider;
}

export function buildProvidersConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Verification providers",
    listTitle: "Verification Providers",
    listDescription:
      "Manage provider registry entries used by the platform-admin operations console.",
    detailBreadcrumbLabel: "Verification Providers",
    searchPlaceholder: "Search verification providers...",
    createLabel: "Add provider",
    exportLabel: "Export",
    filters: ["Status", "Type", "Owner"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Type", value: record.primaryMeta, helper: "provider class" },
      { label: "Code", value: record.secondaryMeta, helper: "registry code" },
      { label: "Config", value: record.tertiaryMeta, helper: "settings" },
      { label: "Updated", value: record.updatedAt, helper: "backend" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Provider record",
        description: "Backend provider registry details.",
        items: [
          { label: "Name", value: record.title },
          { label: "Status", value: record.status },
          { label: "Last updated", value: record.updatedAt },
        ],
      },
    ],
  };
}
