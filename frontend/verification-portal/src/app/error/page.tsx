"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@identitycore/ui";
import { VerificationShell } from "@/components/layout/verification-shell";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <VerificationShell>
      <div className="mx-auto max-w-xl rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-700">
          <AlertTriangle className="h-6 w-6" />
        </div>

        <h1 className="mt-6 text-3xl font-semibold tracking-tight">
          Something went wrong
        </h1>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          The verification flow could not load. Try again.
        </p>

        <Button onClick={reset} className="mt-6 rounded-xl">
          Try again
        </Button>
      </div>
    </VerificationShell>
  );
}
