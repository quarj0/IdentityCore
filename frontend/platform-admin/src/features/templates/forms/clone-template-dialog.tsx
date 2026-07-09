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

type CloneTemplateDialogProps = {
  templateName: string;
};

export function CloneTemplateDialog({ templateName }: CloneTemplateDialogProps) {
  const [name, setName] = useState(`${templateName} Copy`);

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
          <DialogTitle>Clone template</DialogTitle>
          <DialogDescription>
            Create a new draft from {templateName}. The cloned template can be edited before publishing.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="clone-name">New template name</Label>
          <Input
            id="clone-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!name.trim()}>Clone template</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}