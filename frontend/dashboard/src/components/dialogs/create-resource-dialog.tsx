"use client";

import { Plus } from "lucide-react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Input,
  Label,
  Textarea,
} from "@identitycore/ui";

interface CreateResourceDialogProps {
  title: string;
  triggerLabel: string;
  nameLabel?: string;
  descriptionLabel?: string;
}

export function CreateResourceDialog({
  title,
  triggerLabel,
  nameLabel = "Name",
  descriptionLabel = "Description",
}: CreateResourceDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button type="button" className="rounded-xl">
          <Plus className="h-4 w-4" />
          {triggerLabel}
        </Button>
      </DialogTrigger>

      <DialogContent className="rounded-3xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <form className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="resourceName">{nameLabel}</Label>
            <Input id="resourceName" placeholder="Enter name" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="resourceDescription">{descriptionLabel}</Label>
            <Textarea id="resourceDescription" placeholder="Optional details" />
          </div>

          <Button type="button" className="w-full rounded-xl">
            Create
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
