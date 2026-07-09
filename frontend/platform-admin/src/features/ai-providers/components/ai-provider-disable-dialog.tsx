"use client";

import { useState } from "react";
import { PowerOff } from "lucide-react";
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

type AiProviderDisableDialogProps = {
  providerName: string;
};

export function AiProviderDisableDialog({
  providerName,
}: AiProviderDisableDialogProps) {
  const [reason, setReason] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <PowerOff className="mr-2 size-4" aria-hidden="true" />
          Disable
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Disable {providerName}?</DialogTitle>
          <DialogDescription>
            Disabling this provider may affect verification routing, fallback behavior and active workflows.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="disable-provider-reason">Reason</Label>
          <Textarea
            id="disable-provider-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this provider is being disabled..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" disabled={!reason.trim()}>
            Disable provider
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}