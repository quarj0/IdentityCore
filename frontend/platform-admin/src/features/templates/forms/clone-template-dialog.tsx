"use client";

import { useState } from "react";
import { cloneTemplate } from "@/features/templates/live-data";
import { Copy } from "lucide-react";
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

type CloneTemplateDialogProps = {
  templateName: string;
  templateId: string;
  onComplete?: () => void;
};

export function CloneTemplateDialog({ templateName, templateId, onComplete }: CloneTemplateDialogProps) {
  const [name, setName] = useState(`${templateName} Copy`);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => { setSubmitting(true); setError(null); try { await cloneTemplate(templateId, name); onComplete?.(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to clone template."); } finally { setSubmitting(false); } };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Copy className="mr-2 size-4" aria-hidden="true" />
          Clone
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Clone template</DialogTitle>
          <DialogDescription>
            Create a new draft from {templateName}. The cloned template can be edited before publishing.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="clone-name">New template name</Label>
          <Input
            id="clone-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>

        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button onClick={submit} disabled={submitting || !name.trim()}>{submitting ? "Cloning…" : "Clone template"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}