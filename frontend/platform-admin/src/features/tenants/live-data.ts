"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type Tenant = {
  id: string;
  organizationId: string;
  organizationName: string;
  organizationStatus: string;
  name: string;
  slug: string;
  status: string;
  settings: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

type TenantResponse = {
  platformTenants: Tenant[];
  platformTenant: Tenant | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "active") return "success";
  if (status === "pending_review") return "warning";
  if (status === "suspended") return "danger";
  return "info";
}

function toRecord(tenant: Tenant): AdminRecord {
  return {
    id: tenant.id,
    title: tenant.name,
    subtitle: `${tenant.organizationName} · ${tenant.slug}`,
    status: tenant.status,
    statusTone: tone(tenant.status),
    primaryMeta: tenant.organizationName,
    secondaryMeta: tenant.organizationStatus,
    tertiaryMeta: `Settings keys: ${Object.keys(tenant.settings || {}).length}`,
    owner: tenant.organizationId,
    updatedAt: formatDateTime(tenant.updatedAt),
    href: `/tenants/${tenant.id}`,
  };
}

export function tenantRecordToAdminRecord(tenant: Tenant): AdminRecord {
  return toRecord(tenant);
}

export async function fetchTenantRecords() {
  const data = await graphqlRequest<TenantResponse>(
    `
      query PlatformTenants {
        platformTenants {
          id
          organizationId
          organizationName
          organizationStatus
          name
          slug
          status
          settings
          createdAt
          updatedAt
        }
      }
    `,
  );
  return data.platformTenants.map(toRecord);
}

export async function fetchTenantRecord(tenantId: string) {
  const data = await graphqlRequest<TenantResponse>(
    `
      query PlatformTenant($tenantId: String!) {
        platformTenant(tenantId: $tenantId) {
          id
          organizationId
          organizationName
          organizationStatus
          name
          slug
          status
          settings
          createdAt
          updatedAt
        }
      }
    `,
    { tenantId },
  );
  return data.platformTenant;
}

export function buildTenantConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Platform infrastructure",
    listTitle: "Tenants",
    listDescription:
      "Monitor tenant environments, lifecycle status, settings and organization linkage using live backend data.",
    detailBreadcrumbLabel: "Tenants",
    searchPlaceholder: "Search tenants...",
    createLabel: "Provision tenant",
    exportLabel: "Export",
    filters: ["Status", "Region", "Environment"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Organization", value: record.primaryMeta, helper: "parent organization" },
      { label: "Status", value: record.status, helper: "tenant state" },
      { label: "Settings", value: record.tertiaryMeta, helper: "config keys" },
      { label: "Updated", value: record.updatedAt, helper: "backend" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Tenant",
        description: "Tenant identity and routing information.",
        items: [
          { label: "Tenant", value: record.title },
          { label: "Organization", value: record.primaryMeta },
          { label: "Organization status", value: record.secondaryMeta },
          { label: "Slug", value: record.subtitle },
        ],
      },
      {
        title: "Platform settings",
        description: "Tenant settings currently stored in the backend.",
        items: [
          { label: "Settings key count", value: record.tertiaryMeta },
          { label: "Parent org id", value: record.owner },
          { label: "Last updated", value: record.updatedAt },
        ],
      },
    ],
  };
}
