"use client";

import { useState } from "react";
import { archiveWorkflow } from "@/features/workflows/live-data";
import { Archive } from "lucide-react";
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

type WorkflowArchiveDialogProps = {
  workflowName: string;
  workflowId: string;
  onComplete?: () => void;
};

export function WorkflowArchiveDialog({ workflowName, workflowId, onComplete }: WorkflowArchiveDialogProps) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => { setSubmitting(true); setError(null); try { await archiveWorkflow(workflowId); onComplete?.(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to archive workflow."); } finally { setSubmitting(false); } };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Archive className="mr-2 size-4" aria-hidden="true" />
          Archive
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Archive {workflowName}?</DialogTitle>
          <DialogDescription>
            Archived workflows remain visible in history but cannot be used for new organization workflows.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="workflow-archive-reason">Archive reason</Label>
          <Textarea
            id="workflow-archive-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this workflow is being archived..."
          />
        </div>

        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" onClick={submit} disabled={submitting || !reason.trim()}>{submitting ? "Archiving…" : "Archive workflow"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}