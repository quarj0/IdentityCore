"use client";

import { AlertTriangle } from "lucide-react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@identitycore/ui";

interface ConfirmationDialogProps {
  triggerLabel: string;
  title: string;
  description: string;
  confirmLabel: string;
}

export function ConfirmationDialog({
  triggerLabel,
  title,
  description,
  confirmLabel,
}: ConfirmationDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive" className="rounded-xl">
          {triggerLabel}
        </Button>
      </DialogTrigger>

      <DialogContent className="rounded-3xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="rounded-2xl bg-red-50 p-4 text-sm leading-6 text-red-800">
          <div className="flex gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
            <p>{description}</p>
          </div>
        </div>

        <Button variant="destructive" className="rounded-xl">
          {confirmLabel}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
