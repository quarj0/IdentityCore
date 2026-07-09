"use client";

import { useState } from "react";
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
};

export function CloneWorkflowDialog({ workflowName }: CloneWorkflowDialogProps) {
  const [name, setName] = useState(`${workflowName} Copy`);

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

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!name.trim()}>Clone workflow</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}