"use client";

import { useState } from "react";
import { ShieldOff } from "lucide-react";
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

type SuspendOrganizationDialogProps = {
  organizationName: string;
};

export function SuspendOrganizationDialog({
  organizationName,
}: SuspendOrganizationDialogProps) {
  const [reason, setReason] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="border-rose-300/20 bg-rose-400/10 text-rose-200 hover:bg-rose-400/20"
        >
          <ShieldOff className="mr-2 size-4" aria-hidden="true" />
          Suspend organization
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Suspend {organizationName}?</DialogTitle>
          <DialogDescription>
            This will block API access, disable verification portals and prevent
            organization users from accessing their workspace.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="suspension-reason">Suspension reason</Label>
          <Textarea
            id="suspension-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this organization is being suspended..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" disabled={!reason.trim()}>
            Confirm suspension
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
