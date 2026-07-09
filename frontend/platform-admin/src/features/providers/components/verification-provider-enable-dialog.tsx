"use client";

import { useState } from "react";
import { PlugZap } from "lucide-react";
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

type VerificationProviderEnableDialogProps = {
  providerName: string;
};

export function VerificationProviderEnableDialog({
  providerName,
}: VerificationProviderEnableDialogProps) {
  const [notes, setNotes] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <PlugZap className="mr-2 size-4" aria-hidden="true" />
          Enable sandbox
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Enable sandbox for {providerName}?</DialogTitle>
          <DialogDescription>
            This will make the provider available for internal testing with mock credentials and non-production traffic.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="provider-enable-notes">Internal notes</Label>
          <Textarea
            id="provider-enable-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Add why this provider is being enabled..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!notes.trim()}>Enable sandbox</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}