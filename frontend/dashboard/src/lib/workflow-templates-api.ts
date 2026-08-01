"use client";

import { restRequest } from "@/lib/api-client";

export type WorkflowTemplate = {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  countries: string[];
  required_checks: string[];
  steps: string[];
  settings: Record<string, unknown>;
  provider_requirements: string[];
  output_claims: string[];
  risk_level: string;
};

export type WorkspaceProject = {
  id: string;
  name: string;
  environment: "sandbox" | "production";
  status: string;
  is_default: boolean;
};

export type InstantiatedWorkflow = {
  id: string;
  project_id: string;
  name: string;
  description: string;
  status: string;
  steps: string[];
  settings: Record<string, unknown>;
  source_template_id: string;
  source_template_version: string;
  created: boolean;
};

export async function fetchWorkflowTemplates() {
  const data = await restRequest<{ results: WorkflowTemplate[] }>(
    "/workflow-templates/",
  );
  return data.results;
}

export async function fetchWorkspaceProjects() {
  const data = await restRequest<{ results: WorkspaceProject[] }>("/projects/");
  return data.results;
}

export async function instantiateWorkflowTemplate(input: {
  projectId: string;
  template: WorkflowTemplate;
  name: string;
  idempotencyKey: string;
}) {
  return restRequest<InstantiatedWorkflow>(
    `/projects/${input.projectId}/workflows:instantiate`,
    {
      method: "POST",
      headers: { "Idempotency-Key": input.idempotencyKey },
      body: JSON.stringify({
        template_id: input.template.id,
        template_version: input.template.version,
        name: input.name,
      }),
    },
  );
}
