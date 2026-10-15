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

export function CreateTemplateDialog({
  onCreated,
}: {
  onCreated?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [requiredChecks, setRequiredChecks] = useState<string[]>(["document"]);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      await createTemplate({
        name,
        description,
        category: category.replace(/-/g, "_"),
        requiredChecks,
        steps: [
          "consent",
          ...(requiredChecks.includes("document") ? ["document"] : []),
          ...(requiredChecks.some((check) =>
            ["liveness", "face_match"].includes(check),
          )
            ? ["selfie"]
            : []),
          ...(requiredChecks.includes("liveness") ? ["liveness"] : []),
          ...(requiredChecks.includes("face_match") ? ["face_match"] : []),
          "decision",
        ],
      });
      setOpen(false);
      setName("");
      setDescription("");
      setCategory("");
      setRequiredChecks(["document"]);
      onCreated?.();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Unable to create template.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
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
            Create an official IdentityCore template for organizations to use or
            clone.
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
            <Label htmlFor="template-category">Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger id="template-category">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="government-id">Government ID</SelectItem>
                <SelectItem value="banking-kyc">Banking KYC</SelectItem>
                <SelectItem value="employment">Employment</SelectItem>
                <SelectItem value="education">Education</SelectItem>
                <SelectItem value="healthcare">Healthcare</SelectItem>
                <SelectItem value="age-verification">
                  Age Verification
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">Required checks</legend>
            {[
              ["document", "Identity document"],
              ["liveness", "Liveness"],
              ["face_match", "Face match"],
            ].map(([value, label]) => (
              <label key={value} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={requiredChecks.includes(value)}
                  disabled={
                    value === "face_match" &&
                    !requiredChecks.includes("document")
                  }
                  onChange={(event) =>
                    setRequiredChecks((current) =>
                      event.target.checked
                        ? [...current, value]
                        : current.filter(
                            (item) =>
                              item !== value &&
                              (value !== "document" || item !== "face_match"),
                          ),
                    )
                  }
                />
                {label}
              </label>
            ))}
          </fieldset>
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
          <Button
            onClick={submit}
            disabled={
              submitting ||
              !name.trim() ||
              !category ||
              !description.trim() ||
              requiredChecks.length === 0
            }
          >
            {submitting ? "Creating…" : "Create draft"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
