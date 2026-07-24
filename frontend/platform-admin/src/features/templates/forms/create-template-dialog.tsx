"use client";

import { useState } from "react";
import { createTemplate } from "@/features/templates/live-data";
import { Plus } from "lucide-react";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from "@identitycore/ui";

export function CreateTemplateDialog({ onCreated }: { onCreated?: () => void }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSubmitting(true); setError(null);
    try {
      await createTemplate({ name, description, category: category.replace(/-/g, "_") });
      onCreated?.();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to create template."); }
    finally { setSubmitting(false); }
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 size-4" aria-hidden="true" />
          Create template
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create global template</DialogTitle>
          <DialogDescription>
            Create an official IdentityCore template for organizations to use or clone.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="template-name">Template name</Label>
            <Input
              id="template-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Example: Ghana Card Standard KYC"
            />
          </div>

          <div className="space-y-2">
            <Label>Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="government-id">Government ID</SelectItem>
                <SelectItem value="banking-kyc">Banking KYC</SelectItem>
                <SelectItem value="employment">Employment</SelectItem>
                <SelectItem value="education">Education</SelectItem>
                <SelectItem value="healthcare">Healthcare</SelectItem>
                <SelectItem value="age-verification">Age Verification</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="template-description">Description</Label>
            <Textarea
              id="template-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Describe what this template verifies..."
            />
          </div>
        </div>

        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button onClick={submit} disabled={submitting || !name.trim() || !category || !description.trim()}>
            {submitting ? "Creating…" : "Create draft"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}