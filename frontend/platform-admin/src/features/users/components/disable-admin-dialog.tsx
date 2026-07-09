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

type DisableAdminDialogProps = {
  adminName: string;
};

export function DisableAdminDialog({ adminName }: DisableAdminDialogProps) {
  const [reason, setReason] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">
          <ShieldOff className="mr-2 size-4" aria-hidden="true" />
          Disable account
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Disable {adminName}?</DialogTitle>
          <DialogDescription>
            This will revoke platform admin access and terminate active
            sessions. The action will be recorded in the platform audit trail.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="disable-reason">Reason</Label>
          <Textarea
            id="disable-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this admin account is being disabled..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" disabled={!reason.trim()}>
            Disable admin
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
