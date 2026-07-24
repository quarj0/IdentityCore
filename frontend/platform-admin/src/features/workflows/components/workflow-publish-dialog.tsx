"use client";

import { useState } from "react";
import { publishWorkflow } from "@/features/workflows/live-data";
import { UploadCloud } from "lucide-react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Label,
  Textarea,
} from "@identitycore/ui";

type WorkflowPublishDialogProps = {
  workflowName: string;
  workflowId: string;
  onComplete?: () => void;
};

export function WorkflowPublishDialog({ workflowName, workflowId, onComplete }: WorkflowPublishDialogProps) {
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => { setSubmitting(true); setError(null); try { await publishWorkflow(workflowId); onComplete?.(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to publish workflow."); } finally { setSubmitting(false); } };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <UploadCloud className="mr-2 size-4" aria-hidden="true" />
          Publish
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Publish {workflowName}?</DialogTitle>
          <DialogDescription>
            Publishing makes this workflow available in the official workflow library.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="workflow-publish-notes">Release notes</Label>
          <Textarea
            id="workflow-publish-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Describe what changed in this workflow version..."
          />
        </div>

        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button onClick={submit} disabled={submitting || !notes.trim()}>{submitting ? "Publishing…" : "Publish workflow"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}