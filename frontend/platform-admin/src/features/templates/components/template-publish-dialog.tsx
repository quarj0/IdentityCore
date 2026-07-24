"use client";

import { useState } from "react";
import { publishTemplate } from "@/features/templates/live-data";
import { UploadCloud } from "lucide-react";
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

type TemplatePublishDialogProps = {
  templateName: string;
  templateId: string;
  onComplete?: () => void;
};

export function TemplatePublishDialog({ templateName, templateId, onComplete }: TemplatePublishDialogProps) {
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => { setSubmitting(true); setError(null); try { await publishTemplate(templateId); onComplete?.(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to publish template."); } finally { setSubmitting(false); } };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <UploadCloud className="mr-2 size-4" aria-hidden="true" />
          Publish
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Publish {templateName}?</DialogTitle>
          <DialogDescription>
            Publishing makes this template available to organizations from the official template library.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="publish-notes">Release notes</Label>
          <Textarea
            id="publish-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Describe what changed in this version..."
          />
        </div>

        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button onClick={submit} disabled={submitting || !notes.trim()}>{submitting ? "Publishing…" : "Publish template"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}