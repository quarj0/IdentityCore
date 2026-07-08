import Link from "next/link";
import { AlertTriangle, CheckCircle2, CircleDashed } from "lucide-react";
import { Button } from "@identitycore/ui";
import { mockResult, resultStates } from "@/data/mock-session";

interface ResultSummaryProps {
  state?: "approved" | "review" | "rejected";
}

export function ResultSummary({ state = "approved" }: ResultSummaryProps) {
  const result = resultStates[state];

  const tone =
    state === "approved"
      ? "border-blue-100 bg-blue-50 text-blue-950"
      : state === "review"
        ? "border-amber-100 bg-amber-50 text-amber-950"
        : "border-red-100 bg-red-50 text-red-950";

  const Icon =
    state === "approved"
      ? CheckCircle2
      : state === "review"
        ? CircleDashed
        : AlertTriangle;

  return (
    <div className="space-y-6">
      <div className={`rounded-[2rem] border p-6 ${tone}`}>
        <div className="flex items-center gap-3">
          <Icon className="h-8 w-8" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium">Verification decision</p>
            <h2 className="mt-1 text-3xl font-semibold">{result.decision}</h2>
            <p className="mt-2 text-sm leading-6">{result.description}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
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

      <Button asChild size="lg" className="w-full rounded-xl">
        <Link href="/completed">Finish verification</Link>
      </Button>
    </div>
  );
}
