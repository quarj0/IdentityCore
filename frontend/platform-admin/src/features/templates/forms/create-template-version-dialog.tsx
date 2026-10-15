"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createTemplateVersion } from "@/features/templates/live-data";
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
} from "@identitycore/ui";

export function CreateTemplateVersionDialog({
  templateId,
  templateName,
  sourceVersion,
}: {
  templateId: string;
  templateName: string;
  sourceVersion: string;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [version, setVersion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const created = await createTemplateVersion(templateId, version.trim());
      setOpen(false);
      router.push(`/templates/${created.id}`);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create template version.",
      );
    } finally {
      setSubmitting(false);
    }
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">New version</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create template version</DialogTitle>
          <DialogDescription>
            Create an editable draft of {templateName} with a version later than{" "}
            {sourceVersion}. The published source remains available.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="template-version">New version</Label>
          <Input
            id="template-version"
            value={version}
            onChange={(event) => setVersion(event.target.value)}
            placeholder="1.1"
          />
        </div>
        {error ? (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        ) : null}
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button onClick={submit} disabled={submitting || !version.trim()}>
            {submitting ? "Creating…" : "Create version"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
