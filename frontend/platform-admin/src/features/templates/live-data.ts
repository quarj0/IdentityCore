"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

export type TemplateRecord = {
  id: string;
  name: string;
  description: string;
  category: string;
  status: string;
  version: string;
  countries: string[];
  requiredChecks: string[];
  usageCount: number;
  clonedByOrganizations: number;
  ownerTeam: string;
  riskLevel: string;
  createdById: string;
  createdByEmail: string;
  createdAt: string;
  updatedAt: string;
};

type TemplateResponse = {
  platformTemplates: TemplateRecord[];
  platformTemplate: TemplateRecord | null;
};

function tone(status: string): AdminRecord["statusTone"] {
  if (status === "published") return "success";
  if (status === "draft") return "warning";
  if (status === "archived") return "neutral";
  return "info";
}

export function templateRecordToAdminRecord(template: TemplateRecord): AdminRecord {
  return {
    id: template.id,
    title: template.name,
    subtitle: template.description,
    status: template.status,
    statusTone: tone(template.status.toLowerCase()),
    primaryMeta: template.category,
    secondaryMeta: template.version,
    tertiaryMeta: `${template.countries.length} countries`,
    owner: template.ownerTeam,
    updatedAt: formatDateTime(template.updatedAt),
    href: `/templates/${template.id}`,
  };
}

export async function fetchTemplateRecords() {
  const data = await graphqlRequest<TemplateResponse>(
    `
      query PlatformTemplates($page: Int!, $pageSize: Int!) {
        platformTemplates(page: $page, pageSize: $pageSize) {
          id
          name
          description
          category
          status
          version
          countries
          requiredChecks
          usageCount
          clonedByOrganizations
          ownerTeam
          riskLevel
          createdById
          createdByEmail
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformTemplates;
}

export async function fetchTemplateRecord(templateId: string) {
  const data = await graphqlRequest<TemplateResponse>(
    `
      query PlatformTemplate($templateId: String!) {
        platformTemplate(templateId: $templateId) {
          id
          name
          description
          category
          status
          version
          countries
          requiredChecks
          usageCount
          clonedByOrganizations
          ownerTeam
          riskLevel
          createdById
          createdByEmail
          createdAt
          updatedAt
        }
      }
    `,
    { templateId },
  );
  return data.platformTemplate;
}

export function toTemplateRecord(template: TemplateRecord) {
  return template;
}

export function buildTemplateConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Templates",
    listTitle: "Templates",
    listDescription:
      "Manage reusable verification templates, policy bundles and operational defaults.",
    detailBreadcrumbLabel: "Templates",
    searchPlaceholder: "Search templates...",
    createLabel: "Create template",
    exportLabel: "Export templates",
    filters: ["Status", "Category", "Risk"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Category", value: record.primaryMeta, helper: "template class" },
      { label: "Version", value: record.secondaryMeta, helper: "release" },
      { label: "Countries", value: record.tertiaryMeta, helper: "coverage" },
      { label: "Owner", value: record.owner, helper: "team" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Template controls",
        description: "Live template settings from the backend.",
        items: [
          { label: "Status", value: record.status },
          { label: "Version", value: record.secondaryMeta },
          { label: "Usage", value: "Used as a reusable workflow preset." },
          { label: "Updated", value: record.updatedAt },
        ],
      },
    ],
  };
}

export async function createTemplate(input: { name: string; description: string; category: string }) {
  const data = await graphqlRequest<{ createPlatformTemplate: TemplateRecord }>(
    `mutation CreatePlatformTemplate($name: String!, $description: String!, $category: String!) {
      createPlatformTemplate(name: $name, description: $description, category: $category) {
        id name description category status version countries requiredChecks usageCount
        clonedByOrganizations ownerTeam riskLevel createdById createdByEmail createdAt updatedAt
      }
    }`, input,
  );
  return data.createPlatformTemplate;
}
