"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type PlatformSetting = {
  id: string;
  title: string;
  category: string;
  status: string;
  primaryValue: string;
  secondaryValue: string;
  ownerTeam: string;
  description: string;
  updatedAt: string;
};

type SettingsResponse = {
  platformSettings: PlatformSetting[];
  platformSetting: PlatformSetting | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "configured" || status === "enabled") return "success";
  if (status === "unconfigured" || status === "review_needed") return "warning";
  return "info";
}

function toRecord(setting: PlatformSetting): AdminRecord {
  return {
    id: setting.id,
    title: setting.title,
    subtitle: setting.description,
    status: setting.status,
    statusTone: tone(setting.status),
    primaryMeta: setting.primaryValue,
    secondaryMeta: setting.secondaryValue,
    tertiaryMeta: setting.category,
    owner: setting.ownerTeam,
    updatedAt: formatDateTime(setting.updatedAt),
    href: `/settings/${setting.id}`,
  };
}

export async function fetchSettingsRecords() {
  const data = await graphqlRequest<SettingsResponse>(
    `
      query PlatformSettings {
        platformSettings {
          id
          title
          category
          status
          primaryValue
          secondaryValue
          ownerTeam
          description
          updatedAt
        }
      }
    `,
  );
  return data.platformSettings.map(toRecord);
}

export async function fetchSettingRecord(settingId: string) {
  const data = await graphqlRequest<SettingsResponse>(
    `
      query PlatformSetting($settingId: String!) {
        platformSetting(settingId: $settingId) {
          id
          title
          category
          status
          primaryValue
          secondaryValue
          ownerTeam
          description
          updatedAt
        }
      }
    `,
    { settingId },
  );
  return data.platformSetting;
}

export function buildSettingsConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Platform configuration",
    listTitle: "Settings",
    listDescription:
      "Inspect the live platform settings and backend configuration values used by IdentityCore.",
    detailBreadcrumbLabel: "Settings",
    searchPlaceholder: "Search settings...",
    createLabel: "Add setting",
    exportLabel: "Export",
    filters: ["Category", "Status", "Owner"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Primary", value: record.primaryMeta, helper: "configuration" },
      { label: "Secondary", value: record.secondaryMeta, helper: "configuration" },
      { label: "Category", value: record.tertiaryMeta, helper: "area" },
      { label: "Updated", value: record.updatedAt, helper: "backend" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Configuration",
        description: "Live backend settings values.",
        items: [
          { label: "Setting", value: record.title },
          { label: "Description", value: record.subtitle },
          { label: "Status", value: record.status },
          { label: "Owner team", value: record.owner },
        ],
      },
      {
        title: "Values",
        description: "Primary and secondary configuration values.",
        items: [
          { label: "Primary value", value: record.primaryMeta },
          { label: "Secondary value", value: record.secondaryMeta },
          { label: "Updated", value: record.updatedAt },
        ],
      },
    ],
  };
}

export function settingToAdminRecord(setting: PlatformSetting): AdminRecord {
  return toRecord(setting);
}
