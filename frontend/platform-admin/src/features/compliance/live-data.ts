"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type VerificationPolicy = {
  id: string;
  name: string;
  description: string;
  version: number;
  status: string;
  requiredDocumentTypes: string[];
  requiredLivenessLevel: string;
  faceMatchThreshold: number;
  manualReviewThreshold: number;
  verificationExpiryMinutes: number;
  mediaRetentionDays: number;
  metadataRetentionDays: number;
  createdAt: string;
  updatedAt: string;
};

type ComplianceResponse = {
  platformVerificationPolicies: VerificationPolicy[];
  platformVerificationPolicy: VerificationPolicy | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active") return "success";
  if (status === "draft") return "warning";
  if (status === "archived") return "neutral";
  return "info";
}

export function compliancePolicyToRecord(policy: VerificationPolicy): AdminRecord {
  return {
    id: policy.id,
    title: policy.name,
    subtitle: policy.description || `${policy.name} policy version ${policy.version}`,
    status: policy.status,
    statusTone: tone(policy.status.toLowerCase()),
    primaryMeta: `${policy.requiredDocumentTypes.length} document types`,
    secondaryMeta: policy.requiredLivenessLevel,
    tertiaryMeta: `Retention ${policy.mediaRetentionDays} days`,
    owner: `v${policy.version}`,
    updatedAt: formatDateTime(policy.updatedAt),
    href: `/compliance/${policy.id}`,
  };
}

export async function fetchComplianceRecords() {
  const data = await graphqlRequest<ComplianceResponse>(
    `
      query PlatformVerificationPolicies($page: Int!, $pageSize: Int!) {
        platformVerificationPolicies(page: $page, pageSize: $pageSize) {
          id
          name
          description
          version
          status
          requiredDocumentTypes
          requiredLivenessLevel
          faceMatchThreshold
          manualReviewThreshold
          verificationExpiryMinutes
          mediaRetentionDays
          metadataRetentionDays
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformVerificationPolicies.map(compliancePolicyToRecord);
}

export async function fetchComplianceRecord(policyId: string) {
  const data = await graphqlRequest<ComplianceResponse>(
    `
      query PlatformVerificationPolicy($policyId: String!) {
        platformVerificationPolicy(policyId: $policyId) {
          id
          name
          description
          version
          status
          requiredDocumentTypes
          requiredLivenessLevel
          faceMatchThreshold
          manualReviewThreshold
          verificationExpiryMinutes
          mediaRetentionDays
          metadataRetentionDays
          createdAt
          updatedAt
        }
      }
    `,
    { policyId },
  );
  return data.platformVerificationPolicy;
}

export function buildComplianceConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Compliance",
    listTitle: "Compliance",
    listDescription:
      "Manage compliance policies from the platform-admin console.",
    detailBreadcrumbLabel: "Compliance",
    searchPlaceholder: "Search compliance policies...",
    createLabel: "Create policy",
    exportLabel: "Export policies",
    filters: ["Status", "Framework", "Retention"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Documents", value: record.primaryMeta, helper: "policy coverage" },
      { label: "Liveness", value: record.secondaryMeta, helper: "required level" },
      { label: "Retention", value: record.tertiaryMeta, helper: "data retention" },
      { label: "Version", value: record.owner, helper: "current" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Policy controls",
        description: "Core compliance controls applied by this policy.",
        items: [
          { label: "Status", value: record.status },
          { label: "Retention", value: record.tertiaryMeta },
          { label: "Updated", value: record.updatedAt },
        ],
      },
    ],
  };
}
