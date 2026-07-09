"use client";

import { useState } from "react";
import { Wrench } from "lucide-react";
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
  Textarea,
} from "@identitycore/ui";

type TenantMaintenanceDialogProps = {
  tenantName: string;
};

export function TenantMaintenanceDialog({
  tenantName,
}: TenantMaintenanceDialogProps) {
  const [reason, setReason] = useState("");
  const [duration, setDuration] = useState("30 minutes");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <Wrench className="mr-2 size-4" aria-hidden="true" />
          Schedule maintenance
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Schedule maintenance</DialogTitle>
          <DialogDescription>
            Schedule a maintenance window for {tenantName}. This action should
            be recorded in audit logs and incident history.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="maintenance-duration">Duration</Label>
            <Input
              id="maintenance-duration"
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
              placeholder="Example: 30 minutes"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="maintenance-reason">Reason</Label>
            <Textarea
              id="maintenance-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Explain why this tenant needs maintenance..."
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!reason.trim() || !duration.trim()}>
            Schedule window
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
