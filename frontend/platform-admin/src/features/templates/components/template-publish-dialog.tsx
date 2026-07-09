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

type TemplatePublishDialogProps = {
  templateName: string;
};

export function TemplatePublishDialog({ templateName }: TemplatePublishDialogProps) {
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
          <DialogTitle>Publish {templateName}?</DialogTitle>
          <DialogDescription>
            Publishing makes this template available to organizations from the official template library.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="publish-notes">Release notes</Label>
          <Textarea
            id="publish-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Describe what changed in this version..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!notes.trim()}>Publish template</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}