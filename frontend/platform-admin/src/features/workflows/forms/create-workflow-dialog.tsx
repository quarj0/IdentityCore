"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Input,
  Label,
  Textarea,
} from "@identitycore/ui";
import { createWorkflow } from "@/features/workflows/live-data";
import {
  defaultWorkflowSteps,
  WorkflowStepsEditor,
  type WorkflowStep,
} from "./workflow-steps-editor";

export function CreateWorkflowDialog({
  onCreated,
}: {
  onCreated?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [steps, setSteps] = useState<WorkflowStep[]>(defaultWorkflowSteps);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await createWorkflow({ tenantId, projectId, name, description, steps });
      setOpen(false);
      setName("");
      setDescription("");
      setSteps(defaultWorkflowSteps);
      onCreated?.();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Unable to create workflow.",
      );
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 size-4" aria-hidden="true" />
          Create workflow
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create workflow</DialogTitle>
          <DialogDescription>
            Create a tenant and project-scoped workflow draft.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="workflow-tenant">Tenant ID</Label>
            <Input
              id="workflow-tenant"
              value={tenantId}
              onChange={(event) => setTenantId(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="workflow-project">Project ID</Label>
            <Input
              id="workflow-project"
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="workflow-name">Workflow name</Label>
            <Input
              id="workflow-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="workflow-description">Description</Label>
            <Textarea
              id="workflow-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          <WorkflowStepsEditor steps={steps} onChange={setSteps} />
        </div>
        {error ? (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        ) : null}
        <DialogFooter>
          <Button
            onClick={submit}
            disabled={submitting || !tenantId || !projectId || !name.trim()}
          >
            {submitting ? "Creating…" : "Create draft"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
