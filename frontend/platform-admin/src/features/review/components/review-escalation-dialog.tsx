"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";
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

type ReviewEscalationDialogProps = {
  caseId: string;
};

export function ReviewEscalationDialog({ caseId }: ReviewEscalationDialogProps) {
  const [reason, setReason] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <AlertTriangle className="mr-2 size-4" aria-hidden="true" />
          Escalate
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Escalate review case</DialogTitle>
          <DialogDescription>
            Escalate {caseId} for senior review, compliance review or fraud investigation.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="escalation-reason">Escalation reason</Label>
          <Textarea
            id="escalation-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this case needs escalation..."
          />
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" disabled={!reason.trim()}>
            Escalate case
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}