"use client";

import { useState } from "react";
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
};

export function WorkflowPublishDialog({ workflowName }: WorkflowPublishDialogProps) {
  const [notes, setNotes] = useState("");

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

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!notes.trim()}>Publish workflow</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}