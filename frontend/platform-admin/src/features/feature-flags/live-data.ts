"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type FeatureFlag = {
  id: string;
  key: string;
  title: string;
  description: string;
  status: string;
  rolloutPercent: number;
  audience: string;
  ownerTeam: string;
  channel: string;
  metadata: Record<string, unknown>;
  createdById: string;
  createdByEmail: string;
  createdAt: string;
  updatedAt: string;
};

type FeatureFlagResponse = {
  platformFeatureFlags: FeatureFlag[];
  platformFeatureFlag: FeatureFlag | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "enabled") return "success";
  if (status === "disabled") return "neutral";
  if (status === "rolling out") return "warning";
  return "info";
}

export function featureFlagRecordToAdminRecord(flag: FeatureFlag): AdminRecord {
  return {
    id: flag.id,
    title: flag.title,
    subtitle: flag.description,
    status: flag.status,
    statusTone: tone(flag.status.toLowerCase()),
    primaryMeta: `${flag.rolloutPercent}% rollout`,
    secondaryMeta: flag.channel,
    tertiaryMeta: flag.audience,
    owner: flag.ownerTeam,
    updatedAt: formatDateTime(flag.updatedAt),
    href: `/feature-flags/${flag.id}`,
  };
}

export async function fetchFeatureFlagRecords() {
  const data = await graphqlRequest<FeatureFlagResponse>(
    `
      query PlatformFeatureFlags($page: Int!, $pageSize: Int!) {
        platformFeatureFlags(page: $page, pageSize: $pageSize) {
          id
          key
          title
          description
          status
          rolloutPercent
          audience
          ownerTeam
          channel
          metadata
          createdById
          createdByEmail
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformFeatureFlags.map(featureFlagRecordToAdminRecord);
}

export async function fetchFeatureFlagRecord(flagId: string) {
  const data = await graphqlRequest<FeatureFlagResponse>(
    `
      query PlatformFeatureFlag($flagId: String!) {
        platformFeatureFlag(flagId: $flagId) {
          id
          key
          title
          description
          status
          rolloutPercent
          audience
          ownerTeam
          channel
          metadata
          createdById
          createdByEmail
          createdAt
          updatedAt
        }
      }
    `,
    { flagId },
  );
  return data.platformFeatureFlag;
}

export function buildFeatureFlagConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Release controls",
    listTitle: "Feature Flags",
    listDescription:
      "Enable, disable and gradually roll out beta features across the IdentityCore platform.",
    detailBreadcrumbLabel: "Feature Flags",
    searchPlaceholder: "Search feature flags...",
    createLabel: "Create flag",
    exportLabel: "Export flags",
    filters: ["Status", "Rollout", "Owner"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Rollout", value: record.primaryMeta, helper: "percentage" },
      { label: "Channel", value: record.secondaryMeta, helper: "release track" },
      { label: "Audience", value: record.tertiaryMeta, helper: "target" },
      { label: "Owner", value: record.owner, helper: "team" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Rollout configuration",
        description: "Current rollout behavior and targeting rules.",
        items: [
          { label: "Status", value: record.status },
          { label: "Rollout", value: record.primaryMeta },
          { label: "Audience", value: record.tertiaryMeta },
          {
            label: "Rollback",
            value:
              "One-click rollback should disable the flag and notify audit/security channels.",
          },
        ],
      },
      {
        title: "Safety checks",
        description: "Controls required before expanding rollout.",
        items: [
          {
            label: "Monitoring",
            value:
              "Track errors, latency, user impact and support tickets after rollout changes.",
          },
          {
            label: "Approval",
            value: "Production rollout above 50% requires product and engineering approval.",
          },
        ],
      },
    ],
  };
}
