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

type TemplateArchiveDialogProps = {
  templateName: string;
};

export function TemplateArchiveDialog({ templateName }: TemplateArchiveDialogProps) {
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
          <DialogTitle>Archive {templateName}?</DialogTitle>
          <DialogDescription>
            Archived templates stay visible in history but cannot be selected for new workflows.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="archive-reason">Archive reason</Label>
          <Textarea
            id="archive-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this template is being archived..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" disabled={!reason.trim()}>
            Archive template
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}