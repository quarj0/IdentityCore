"use client";

import { useState } from "react";
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
import { updateWorkflow, type WorkflowRecord } from "../live-data";
import {
  isWorkflowStep,
  WorkflowStepsEditor,
  type WorkflowStep,
} from "./workflow-steps-editor";

export function EditWorkflowDialog({
  workflow,
  onChanged,
}: {
  workflow: WorkflowRecord;
  onChanged?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(workflow.name);
  const [description, setDescription] = useState(workflow.description);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const supported = workflow.steps.every(isWorkflowStep);
  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await updateWorkflow(workflow.id, { name, description, steps });
      setOpen(false);
      onChanged?.();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Unable to update workflow.",
      );
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) {
          setName(workflow.name);
          setDescription(workflow.description);
          setSteps(workflow.steps.filter(isWorkflowStep));
          setError(null);
        }
        setOpen(next);
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" disabled={workflow.status === "archived"}>
          Edit draft
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit workflow draft</DialogTitle>
          <DialogDescription>
            Changes return a published workflow to draft. Existing published
            versions keep their original steps and policy.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-workflow-name">Workflow name</Label>
            <Input
              id="edit-workflow-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-workflow-description">Description</Label>
            <Textarea
              id="edit-workflow-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          {supported ? (
            <WorkflowStepsEditor steps={steps} onChange={setSteps} />
          ) : (
            <p role="alert">
              This workflow contains unsupported legacy step data. Correct it
              through the workflow API before using this editor.
            </p>
          )}
        </div>
        {error ? (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        ) : null}
        <DialogFooter>
          <Button
            disabled={
              submitting ||
              !supported ||
              !name.trim() ||
              !steps.includes("consent") ||
              !steps.includes("decision")
            }
            onClick={submit}
          >
            {submitting ? "Saving…" : "Save draft"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
