"use client";

import { useState } from "react";
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
};

export function WorkflowArchiveDialog({ workflowName }: WorkflowArchiveDialogProps) {
  const [reason, setReason] = useState("");

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

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" disabled={!reason.trim()}>
            Archive workflow
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}