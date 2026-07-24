"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";

export type WorkflowRecord = {
  id: string;
  name: string;
  description: string;
  status: string;
  projectName: string;
  version: number;
  stepCount: number;
  steps: Array<string | Record<string, unknown>>;
  settings: Record<string, unknown>;
  createdByEmail: string;
  createdAt: string;
  updatedAt: string;
  currentVersion: number;
};

export type WorkflowVersionRecord = {
  id: string;
  workflowId: string;
  workflowName: string;
  version: number;
  policyName: string;
  publishedByEmail: string;
  publishedAt: string;
};

type WorkflowResponse = {
  platformWorkflows: Array<{
    id: string;
    name: string;
    description: string;
    status: string;
    projectName: string;
    steps: Array<string | Record<string, unknown>>;
    settings: Record<string, unknown>;
    currentVersion: number;
    createdByEmail: string;
    createdAt: string;
    updatedAt: string;
  }>;
  platformWorkflow: WorkflowResponse["platformWorkflows"][number] | null;
  platformWorkflowVersions: WorkflowVersionRecord[];
};

function toWorkflowRecord(workflow: WorkflowResponse["platformWorkflows"][number]): WorkflowRecord {
  return {
    ...workflow,
    version: workflow.currentVersion,
    stepCount: workflow.steps.length,
  };
}

function statusTone(status: string) {
  if (status === "published") return "success";
  if (status === "draft") return "warning";
  if (status === "archived") return "neutral";
  return "info";
}

export function workflowStatusTone(status: string) {
  return statusTone(status);
}

export function workflowStatusLabel(status: string) {
  return status.replace(/_/g, " ");
}

export async function fetchWorkflowRecords() {
  const data = await graphqlRequest<WorkflowResponse>(
    `
      query PlatformWorkflows($page: Int!, $pageSize: Int!) {
        platformWorkflows(page: $page, pageSize: $pageSize) {
          id
          name
          description
          status
          projectName
          steps
          settings
          currentVersion
          createdByEmail
          createdAt
          updatedAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformWorkflows.map(toWorkflowRecord);
}

export async function fetchWorkflowRecord(workflowId: string) {
  const data = await graphqlRequest<WorkflowResponse>(
    `
      query PlatformWorkflow($workflowId: String!) {
        platformWorkflow(workflowId: $workflowId) {
          id
          name
          description
          status
          projectName
          steps
          settings
          currentVersion
          createdByEmail
          createdAt
          updatedAt
        }
        platformWorkflowVersions(workflowId: $workflowId) {
          id
          workflowId
          workflowName
          version
          policyName
          publishedByEmail
          publishedAt
        }
      }
    `,
    { workflowId },
  );

  return {
    workflow: data.platformWorkflow ? toWorkflowRecord(data.platformWorkflow) : null,
    versions: data.platformWorkflowVersions,
  };
}

export function normalizeWorkflowStep(step: string | Record<string, unknown>) {
  if (typeof step === "string") {
    return step;
  }

  const label =
    typeof step.label === "string"
      ? step.label
      : typeof step.name === "string"
        ? step.name
        : typeof step.title === "string"
          ? step.title
          : "";

  return label || "Workflow step";
}

export function normalizeLinkedTemplates(settings: Record<string, unknown>) {
  const candidates = [
    settings.linkedTemplates,
    settings.linked_templates,
    settings.templates,
    settings.templateLinks,
    settings.template_links,
  ];
  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      return candidate
        .map((item) => (typeof item === "string" ? item : ""))
        .filter(Boolean);
    }
  }
  return [];
}

export function normalizeWorkflowUsage(workflow: WorkflowRecord) {
  const organizations = workflow.settings.organizations;
  if (!Array.isArray(organizations)) {
    return [];
  }

  return organizations
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const value = item as Record<string, unknown>;
      const organization = typeof value.organization === "string" ? value.organization : "";
      if (!organization) return null;
      return {
        organization,
        environment: typeof value.environment === "string" ? value.environment : "Production",
        runs: typeof value.runs === "number" ? value.runs : 0,
      };
    })
    .filter(Boolean) as Array<{ organization: string; environment: string; runs: number }>;
}

export function normalizeWorkflowVersionHistory(versions: WorkflowVersionRecord[]) {
  return versions.map((version) => ({
    ...version,
    date: formatDateTime(version.publishedAt),
    notes: `${version.policyName} policy`,
    status: "published",
  }));
}

const workflowFields = `id name description status projectName steps settings currentVersion createdByEmail createdAt updatedAt`;
async function runWorkflowMutation(mutation: string, variables: Record<string, unknown>) {
  return graphqlRequest<{ workflow: WorkflowRecord }>(mutation, variables).then((data) => data.workflow);
}
export const cloneWorkflow = (workflowId: string, name: string) =>
  runWorkflowMutation(`mutation CloneWorkflow($workflowId: String!, $name: String!) { workflow: clonePlatformWorkflow(workflowId: $workflowId, name: $name) { ${workflowFields} } }`, { workflowId, name });
export const publishWorkflow = (workflowId: string) =>
  graphqlRequest(`mutation PublishWorkflow($workflowId: String!) { publishPlatformWorkflow(workflowId: $workflowId) { id version } }`, { workflowId });
export const archiveWorkflow = (workflowId: string) =>
  runWorkflowMutation(`mutation ArchiveWorkflow($workflowId: String!) { workflow: archivePlatformWorkflow(workflowId: $workflowId) { ${workflowFields} } }`, { workflowId });
