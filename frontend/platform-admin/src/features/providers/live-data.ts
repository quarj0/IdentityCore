import { restRequest } from "@/lib/admin-api";
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
  provider_type: string;
  status: string;
  configuration: Record<string, unknown>;
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
  if (status === "testing") return "warning";
  if (status === "disabled") return "danger";
  if (status === "deprecated") return "neutral";
  return "info";
}

function toRecord(provider: Provider): AdminRecord {
  return {
    id: provider.id,
    title: provider.name,
    subtitle: `${provider.provider_type.replace(/_/g, " ")} · ${provider.code}`,
    status: provider.status,
    statusTone: tone(provider.status),
    primaryMeta: provider.provider_type,
    secondaryMeta: provider.code,
    tertiaryMeta: `Config keys: ${Object.keys(provider.configuration || {}).length}`,
    owner: "Platform admin",
    updatedAt: formatDate(provider.updated_at),
    href: `/providers/${provider.id}`,
  };
}

export async function fetchVerificationProviderRecords() {
  const data = await restRequest<{ results: Provider[] }>("/platform-admin/providers/");
  return data.results.map(toRecord);
}

export async function fetchVerificationProviderRecord(providerId: string) {
  const provider = await restRequest<Provider>(`/platform-admin/providers/${providerId}`);
  return provider;
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

