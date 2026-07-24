"use client";

import { useState } from "react";
import { archiveTemplate } from "@/features/templates/live-data";
import { Archive } from "lucide-react";
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

type TemplateArchiveDialogProps = {
  templateName: string;
  templateId: string;
  onComplete?: () => void;
};

export function TemplateArchiveDialog({ templateName, templateId, onComplete }: TemplateArchiveDialogProps) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submit = async () => { setSubmitting(true); setError(null); try { await archiveTemplate(templateId); onComplete?.(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to archive template."); } finally { setSubmitting(false); } };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Archive className="mr-2 size-4" aria-hidden="true" />
          Archive
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Archive {templateName}?</DialogTitle>
          <DialogDescription>
            Archived templates stay visible in history but cannot be selected for new workflows.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="archive-reason">Archive reason</Label>
          <Textarea
            id="archive-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Explain why this template is being archived..."
          />
        </div>

        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive" onClick={submit} disabled={submitting || !reason.trim()}>{submitting ? "Archiving…" : "Archive template"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}