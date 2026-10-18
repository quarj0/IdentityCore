"use client";

import { useState } from "react";
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
  DialogClose,
} from "@identitycore/ui";
import { UserPlus } from "lucide-react";
import { invitePlatformAdmin } from "@/features/users/live-data";

type InviteAdminDialogProps = {
  onInvited: () => void;
};

export function InviteAdminDialog({ onInvited }: InviteAdminDialogProps) {
  const [email, setEmail] = useState("");
  const role = "Platform Admin";
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit() {
    setIsSubmitting(true);
    setMessage(null);
    try {
      await invitePlatformAdmin(email, role);
      setMessage(
        `Invitation queued for ${email.trim()}. Delivery status is tracked by the notification service.`,
      );
      setEmail("");
      onInvited();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Unable to send invitation.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <UserPlus className="mr-2 size-4" aria-hidden="true" />
          Invite admin
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite platform admin</DialogTitle>
          <DialogDescription>
            Invite an IdentityCore employee to the internal platform admin
            console.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="admin-email">Email address</Label>
            <Input
              id="admin-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@identitycore.com"
            />
          </div>

          <p className="text-sm text-slate-600">
            This invitation grants full platform administration. Limited
            platform roles are not available.
          </p>
          {message ? (
            <p className="text-sm text-slate-600" role="status">
              {message}
            </p>
          ) : null}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            disabled={
              !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) || isSubmitting
            }
            onClick={submit}
          >
            {isSubmitting ? "Sending…" : "Send invite"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
