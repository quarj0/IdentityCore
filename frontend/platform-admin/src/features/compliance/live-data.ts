import { restRequest } from "@/lib/admin-api";
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
  required_document_types: string[];
  required_liveness_level: string;
  face_match_threshold: number;
  manual_review_threshold: number;
  verification_expiry_minutes: number;
  media_retention_days: number;
  metadata_retention_days: number;
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
    statusTone: tone(policy.status),
    primaryMeta: `${policy.required_document_types.length} document types`,
    secondaryMeta: policy.required_liveness_level,
    tertiaryMeta: `Retention ${policy.media_retention_days} days`,
    owner: `v${policy.version}`,
    updatedAt: formatDate(policy.updated_at),
    href: `/compliance/${policy.id}`,
  };
}

export async function fetchComplianceRecords() {
  const data = await restRequest<{ results: VerificationPolicy[] }>("/platform-admin/policies/");
  return data.results.map(compliancePolicyToRecord);
}

export async function fetchComplianceRecord(policyId: string) {
  const policy = await restRequest<VerificationPolicy>(`/platform-admin/policies/${policyId}`);
  return policy;
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
