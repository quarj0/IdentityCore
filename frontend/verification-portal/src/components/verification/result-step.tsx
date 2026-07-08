import Link from "next/link";
import { AlertTriangle, CheckCircle2, CircleDashed } from "lucide-react";
import { Button } from "@identitycore/ui";
import { CapturePanel } from "./capture-panel";
import { mockResult } from "@/data/verification";

interface ResultStepProps {
  state: "approved" | "review" | "rejected";
  onSubmit: () => void;
}

export function ResultStep({ state, onSubmit }: ResultStepProps) {
  const content = {
    approved: {
      title: "Approved",
      description: "Your verification was completed successfully.",
      className: "border-blue-100 bg-blue-50 text-blue-950",
      icon: CheckCircle2,
    },
    review: {
      title: "Needs review",
      description:
        "Your verification was submitted and requires manual review by the organization.",
      className: "border-amber-100 bg-amber-50 text-amber-950",
      icon: CircleDashed,
    },
    rejected: {
      title: "Rejected",
      description:
        "The verification could not be approved based on the submitted evidence.",
      className: "border-red-100 bg-red-50 text-red-950",
      icon: AlertTriangle,
    },
  }[state];

  const Icon = content.icon;

  return (
    <CapturePanel
      title="Verification result"
      description="Review your verification decision and evidence summary."
    >
      <div className={`rounded-[2rem] border p-6 ${content.className}`}>
        <div className="flex items-center gap-3">
          <Icon className="h-8 w-8" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium">Decision</p>
            <h2 className="mt-1 text-3xl font-semibold">{content.title}</h2>
            <p className="mt-2 text-sm leading-6">{content.description}</p>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {[
          ["Reference", mockResult.reference],
          ["Face match", mockResult.faceMatch],
          ["Liveness", mockResult.liveness],
          ["OCR confidence", mockResult.ocrConfidence],
          ["Document authenticity", mockResult.documentAuthenticity],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-2xl border border-slate-200 bg-white p-4"
          >
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-1 font-semibold">{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Button onClick={onSubmit} size="lg" className="rounded-xl">
          Submit result
        </Button>

        <Button asChild variant="outline" size="lg" className="rounded-xl">
          <Link href="/completed">Finish now</Link>
        </Button>
      </div>
    </CapturePanel>
  );
}
