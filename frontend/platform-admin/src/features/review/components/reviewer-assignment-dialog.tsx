"use client";

import { useState } from "react";
import { UserCheck } from "lucide-react";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@identitycore/ui";

type ReviewerAssignmentDialogProps = {
  caseId: string;
};

export function ReviewerAssignmentDialog({
  caseId,
}: ReviewerAssignmentDialogProps) {
  const [reviewer, setReviewer] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <UserCheck className="mr-2 size-4" aria-hidden="true" />
          Assign reviewer
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Assign reviewer</DialogTitle>
          <DialogDescription>
            Assign a platform reviewer to {caseId}. Assignment changes are saved to the audit log.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label>Reviewer</Label>
          <Select value={reviewer} onValueChange={setReviewer}>
            <SelectTrigger>
              <SelectValue placeholder="Select reviewer" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ama">Ama Mensah</SelectItem>
              <SelectItem value="tunde">Tunde Adebayo</SelectItem>
              <SelectItem value="sarah">Sarah Mitchell</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button disabled={!reviewer}>Assign</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}