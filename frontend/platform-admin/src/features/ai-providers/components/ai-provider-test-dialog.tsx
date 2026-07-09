"use client";

import { useState } from "react";
import { FlaskConical } from "lucide-react";
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

type AiProviderTestDialogProps = {
  providerName: string;
};

export function AiProviderTestDialog({
  providerName,
}: AiProviderTestDialogProps) {
  const [notes, setNotes] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <FlaskConical className="mr-2 size-4" aria-hidden="true" />
          Run test
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Run provider test</DialogTitle>
          <DialogDescription>
            Run a diagnostic test against {providerName}. The result will be saved in the provider health history.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="test-notes">Test notes</Label>
          <Textarea
            id="test-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Describe why this provider test is being run..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!notes.trim()}>Run diagnostic</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}