"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Workflow,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@identitycore/ui";
import { InlineStatus } from "@/components/feedback/inline-status";
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";
import { getErrorMessage } from "@/lib/api-client";
import {
  fetchWorkflowTemplates,
  fetchWorkspaceProjects,
  instantiateWorkflowTemplate,
  type InstantiatedWorkflow,
  type WorkflowTemplate,
  type WorkspaceProject,
} from "@/lib/workflow-templates-api";

const DASHBOARD_URL =
  process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000";

export default function FirstWorkflowPage() {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [project, setProject] = useState<WorkspaceProject | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [workflowName, setWorkflowName] = useState("");
  const [createdWorkflow, setCreatedWorkflow] =
    useState<InstantiatedWorkflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const idempotencyKey = useRef(crypto.randomUUID());

  const selected = useMemo(
    () => templates.find((template) => template.id === selectedId) ?? null,
    [selectedId, templates],
  );

  async function load() {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [availableTemplates, projects] = await Promise.all([
        fetchWorkflowTemplates(),
        fetchWorkspaceProjects(),
      ]);
      const sandbox =
        projects.find(
          (item) => item.environment === "sandbox" && item.is_default,
        ) ??
        projects.find((item) => item.environment === "sandbox") ??
        null;
      setTemplates(availableTemplates);
      setProject(sandbox);
      if (availableTemplates.length > 0) {
        const first = availableTemplates[0];
        setSelectedId((current) => current || first.id);
        setWorkflowName((current) => current || first.name);
      }
      if (!sandbox) {
        setErrorMessage(
          "A sandbox project is required before creating a workflow.",
        );
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    void Promise.all([fetchWorkflowTemplates(), fetchWorkspaceProjects()])
      .then(([availableTemplates, projects]) => {
        if (!active) return;
        const sandbox =
          projects.find(
            (item) => item.environment === "sandbox" && item.is_default,
          ) ??
          projects.find((item) => item.environment === "sandbox") ??
          null;
        setTemplates(availableTemplates);
        setProject(sandbox);
        if (availableTemplates.length > 0) {
          setSelectedId(availableTemplates[0].id);
          setWorkflowName(availableTemplates[0].name);
        }
        if (!sandbox) {
          setErrorMessage(
            "A sandbox project is required before creating a workflow.",
          );
        }
      })
      .catch((error) => {
        if (active) setErrorMessage(getErrorMessage(error));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  function selectTemplate(template: WorkflowTemplate) {
    setSelectedId(template.id);
    setWorkflowName(template.name);
    setErrorMessage(null);
    idempotencyKey.current = crypto.randomUUID();
  }

  async function createWorkflow() {
    if (!selected || !project || !workflowName.trim()) return;
    setSubmitting(true);
    setErrorMessage(null);
    try {
      const workflow = await instantiateWorkflowTemplate({
        projectId: project.id,
        template: selected,
        name: workflowName.trim(),
        idempotencyKey: idempotencyKey.current,
      });
      setCreatedWorkflow(workflow);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <OnboardingPageShell
      eyebrow="First workflow"
      title={
        createdWorkflow
          ? "Your first workflow is ready."
          : "Choose your first identity workflow."
      }
      description={
        createdWorkflow
          ? "The versioned template was copied into your sandbox project and is ready to configure."
          : "Select a published template, review its requirements, and create a sandbox workflow."
      }
      pathname="/onboarding/first-workflow"
    >
      {loading ? (
        <div
          className="flex min-h-64 items-center justify-center"
          aria-label="Loading workflow templates"
        >
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        </div>
      ) : createdWorkflow ? (
        <CreatedWorkflowCard workflow={createdWorkflow} />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1fr_0.62fr]">
          <section className="space-y-4" aria-labelledby="template-list-title">
            <div>
              <h2 id="template-list-title" className="text-xl font-semibold">
                Published templates
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Choose the starting point that matches your first use case.
              </p>
            </div>

            {templates.length === 0 ? (
              <Card className="rounded-3xl border-dashed p-8 text-center">
                <Workflow className="mx-auto h-7 w-7 text-slate-400" />
                <p className="mt-3 font-medium">
                  No published templates are available.
                </p>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {templates.map((template) => {
                  const active = template.id === selectedId;
                  return (
                    <button
                      key={template.id}
                      type="button"
                      aria-pressed={active}
                      onClick={() => selectTemplate(template)}
                      className={`rounded-3xl border p-5 text-left transition ${
                        active
                          ? "border-blue-500 bg-blue-50 ring-2 ring-blue-100"
                          : "border-slate-200 bg-white hover:border-blue-200"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <Badge variant="secondary">
                          {template.category.replaceAll("_", " ")}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          v{template.version}
                        </span>
                      </div>
                      <h3 className="mt-4 font-semibold">{template.name}</h3>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        {template.description}
                      </p>
                      <p className="mt-4 text-xs font-medium text-blue-700">
                        {template.steps.length} workflow steps
                      </p>
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          <Card className="h-fit rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
            <CardHeader>
              <CardTitle>{selected?.name ?? "Select a template"}</CardTitle>
              <CardDescription>
                {selected?.description ??
                  "Choose a published template to review its contract."}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {errorMessage ? (
                <InlineStatus
                  kind="error"
                  title="Unable to create workflow"
                  message={errorMessage}
                  persist
                />
              ) : null}

              {selected ? (
                <>
                  <DefinitionList label="Steps" values={selected.steps} />
                  <DefinitionList
                    label="Provider capabilities"
                    values={selected.provider_requirements}
                  />
                  <DefinitionList
                    label="Output claims"
                    values={selected.output_claims}
                  />
                  <div className="space-y-2">
                    <Label htmlFor="workflowName">Workflow name</Label>
                    <Input
                      id="workflowName"
                      value={workflowName}
                      maxLength={255}
                      onChange={(event) => {
                        setWorkflowName(event.target.value);
                        idempotencyKey.current = crypto.randomUUID();
                      }}
                    />
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4 text-sm text-muted-foreground">
                    Destination: {project?.name ?? "No sandbox project"}
                  </div>
                  <Button
                    size="lg"
                    className="w-full rounded-xl"
                    disabled={!project || !workflowName.trim() || submitting}
                    onClick={() => void createWorkflow()}
                  >
                    {submitting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Workflow className="h-4 w-4" />
                    )}
                    {submitting
                      ? "Creating workflow…"
                      : "Create sandbox workflow"}
                  </Button>
                </>
              ) : null}

              {errorMessage ? (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => void load()}
                >
                  <RefreshCw className="h-4 w-4" /> Retry loading
                </Button>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </OnboardingPageShell>
  );
}

function DefinitionList({
  label,
  values,
}: {
  label: string;
  values: string[];
}) {
  return (
    <div>
      <p className="text-sm font-medium">{label}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {values.length ? (
          values.map((value) => (
            <Badge key={value} variant="outline">
              {value.replaceAll("_", " ")}
            </Badge>
          ))
        ) : (
          <span className="text-sm text-muted-foreground">None specified</span>
        )}
      </div>
    </div>
  );
}

function CreatedWorkflowCard({ workflow }: { workflow: InstantiatedWorkflow }) {
  return (
    <Card className="max-w-2xl rounded-3xl border-emerald-200 bg-white p-2 shadow-sm">
      <CardHeader>
        <CheckCircle2 className="mb-4 h-8 w-8 text-emerald-600" />
        <CardTitle>{workflow.name}</CardTitle>
        <CardDescription>
          Draft created from template version {workflow.source_template_version}{" "}
          with {workflow.steps.length} steps.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button asChild size="lg" className="rounded-xl">
          <Link href={`${DASHBOARD_URL}/workflows/${workflow.id}`}>
            Configure workflow in dashboard <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
