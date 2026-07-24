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
import { deactivatePlatformAdmin } from "@/features/users/live-data";

type DisableAdminDialogProps = {
  adminName: string;
  userId: string;
  onDeactivated: () => void;
};

export function DisableAdminDialog({ adminName, userId, onDeactivated }: DisableAdminDialogProps) {
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit() {
    setSubmitting(true);
    setMessage(null);
    try {
      await deactivatePlatformAdmin(userId, reason);
      setMessage("Platform admin access has been revoked.");
      onDeactivated();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to disable this account.");
    } finally { setSubmitting(false); }
  }

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
          <Button variant="destructive" disabled={!reason.trim() || submitting} onClick={submit}>
            {submitting ? "Disabling…" : "Disable admin"}
          </Button>
        </DialogFooter>
        {message ? <p className="text-sm text-slate-600" role="status">{message}</p> : null}
      </DialogContent>
    </Dialog>
  );
}
