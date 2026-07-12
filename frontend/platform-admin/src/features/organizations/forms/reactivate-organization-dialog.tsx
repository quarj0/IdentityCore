"use client";

import { useState } from "react";
import { RotateCcw } from "lucide-react";
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

type ReactivateOrganizationDialogProps = {
  organizationName: string;
};

export function ReactivateOrganizationDialog({
  organizationName,
}: ReactivateOrganizationDialogProps) {
  const [note, setNote] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button className="bg-emerald-400 text-slate-950 hover:bg-emerald-300">
          <RotateCcw className="mr-2 size-4" aria-hidden="true" />
          Reactivate organization
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reactivate {organizationName}?</DialogTitle>
          <DialogDescription>
            This will restore organization access, API usage and verification
            portal availability.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="reactivation-note">Internal note</Label>
          <Textarea
            id="reactivation-note"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Add an internal note for the audit trail..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!note.trim()}>Confirm reactivation</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
