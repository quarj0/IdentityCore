"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type Organization = {
  id: string;
  name: string;
  slug: string;
  industry: string;
  status: string;
  tenantId: string;
  tenantName: string;
  tenantStatus: string;
  defaultCountryProfileId: string;
  defaultJurisdictionId: string;
  settings: Record<string, unknown>;
  sandboxUsage: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

type OrganizationSupportingDocument = {
  id: string;
  filename: string;
  mimeType: string;
  fileSizeBytes: number;
  status: string;
  uploadedByEmail: string;
  createdAt: string;
};

type OrganizationResponse = {
  platformOrganizations: Organization[];
  platformOrganization: Organization | null;
  platformOrganizationSupportingDocuments: OrganizationSupportingDocument[];
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active") return "success";
  if (status === "pending_review") return "warning";
  if (status === "suspended") return "danger";
  if (status === "rejected") return "danger";
  return "info";
}

function toSizeLabel(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
}

function toRecord(organization: Organization): AdminRecord {
  return {
    id: organization.id,
    title: organization.name,
    subtitle: `${organization.industry} · ${organization.slug}`,
    status: organization.status,
    statusTone: tone(organization.status),
    primaryMeta: organization.tenantName,
    secondaryMeta: organization.tenantStatus,
    tertiaryMeta: organization.defaultCountryProfileId,
    owner: organization.defaultJurisdictionId,
    updatedAt: formatDateTime(organization.updatedAt),
    href: `/organizations/${organization.id}`,
  };
}

export function organizationRecordToAdminRecord(organization: Organization): AdminRecord {
  return toRecord(organization);
}

export async function fetchOrganizationRecords() {
  const data = await graphqlRequest<OrganizationResponse>(
    `
      query PlatformOrganizations {
        platformOrganizations {
          id
          name
          slug
          industry
          status
          tenantId
          tenantName
          tenantStatus
          defaultCountryProfileId
          defaultJurisdictionId
          settings
          sandboxUsage
          createdAt
          updatedAt
        }
      }
    `,
  );
  return data.platformOrganizations.map(toRecord);
}

export async function fetchOrganizationRecord(organizationId: string) {
  const data = await graphqlRequest<OrganizationResponse>(
    `
      query PlatformOrganization($organizationId: String!) {
        platformOrganization(organizationId: $organizationId) {
          id
          name
          slug
          industry
          status
          tenantId
          tenantName
          tenantStatus
          defaultCountryProfileId
          defaultJurisdictionId
          settings
          sandboxUsage
          createdAt
          updatedAt
        }
        platformOrganizationSupportingDocuments(organizationId: $organizationId) {
          id
          filename
          mimeType
          fileSizeBytes
          status
          uploadedByEmail
          createdAt
        }
      }
    `,
    { organizationId },
  );
  return {
    organization: data.platformOrganization,
    supportingDocuments: data.platformOrganizationSupportingDocuments,
  };
}

export function buildOrganizationConfig(
  records: AdminRecord[],
  supportingDocuments: OrganizationSupportingDocument[] = [],
): AdminModuleConfig {
  return {
    moduleLabel: "Platform administration",
    listTitle: "Organizations",
    listDescription:
      "Manage organizations, lifecycle status, onboarding review and operational metadata from live backend data.",
    detailBreadcrumbLabel: "Organizations",
    searchPlaceholder: "Search organizations...",
    createLabel: "Review onboarding",
    exportLabel: "Export",
    filters: ["Status", "Industry", "Country"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Tenant", value: record.primaryMeta, helper: "linked tenant" },
      { label: "Tenant status", value: record.secondaryMeta, helper: "current state" },
      { label: "Country profile", value: record.tertiaryMeta, helper: "default profile" },
      { label: "Jurisdiction", value: record.owner, helper: "default jurisdiction" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Organization",
        description: "Core organization identity and lifecycle details.",
        items: [
          { label: "Organization", value: record.title },
          { label: "Slug", value: record.subtitle },
          { label: "Status", value: record.status },
          { label: "Updated", value: record.updatedAt },
        ],
      },
      {
        title: "Supporting documents",
        description: "Uploaded organizational evidence and current review snapshot.",
        items: supportingDocuments.length
          ? supportingDocuments.map((document) => ({
              label: document.filename,
              value: `${document.status} · ${toSizeLabel(document.fileSizeBytes)} · ${document.uploadedByEmail}`,
            }))
          : [{ label: "Documents", value: "No supporting documents submitted yet." }],
      },
      {
        title: "Backend metadata",
        description: "Raw platform values carried through from the GraphQL backend.",
        items: [
          { label: "Country profile", value: record.tertiaryMeta },
          { label: "Jurisdiction", value: record.owner },
          { label: "Last sync", value: record.updatedAt },
        ],
      },
    ],
  };
}
