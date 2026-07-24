"use client";

import { useState } from "react";
import { cloneWorkflow } from "@/features/workflows/live-data";
import { Copy } from "lucide-react";
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
} from "@identitycore/ui";

type CloneWorkflowDialogProps = {
  workflowName: string;
  workflowId: string;
  onComplete?: () => void;
};

export function CloneWorkflowDialog({ workflowName, workflowId, onComplete }: CloneWorkflowDialogProps) {
  const [name, setName] = useState(`${workflowName} Copy`);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => { setSubmitting(true); setError(null); try { await cloneWorkflow(workflowId, name); onComplete?.(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to clone workflow."); } finally { setSubmitting(false); } };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Copy className="mr-2 size-4" aria-hidden="true" />
          Clone
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Clone workflow</DialogTitle>
          <DialogDescription>
            Create a new draft workflow from {workflowName}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="clone-workflow-name">New workflow name</Label>
          <Input
            id="clone-workflow-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>

        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button onClick={submit} disabled={submitting || !name.trim()}>{submitting ? "Cloning…" : "Clone workflow"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}