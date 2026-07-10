import Link from "next/link";
import { ClockAlert } from "lucide-react";
import { Button } from "@identitycore/ui";
import { VerificationShell } from "@/components/layout/verification-shell";

export default function ExpiredPage() {
  return (
    <VerificationShell>
      <div className="mx-auto max-w-xl rounded-4xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
          <ClockAlert className="h-6 w-6" />
        </div>

        <h1 className="mt-6 text-3xl font-semibold tracking-tight">
          Verification link expired
        </h1>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          This verification session is no longer active. Request a new
          verification link from the organization that sent it.
        </p>

        <Button asChild className="mt-6 rounded-xl">
          <Link href="/">Back home</Link>
        </Button>
      </div>
    </VerificationShell>
  );
}
