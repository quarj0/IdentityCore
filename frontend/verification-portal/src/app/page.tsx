import Link from "next/link";
import { ArrowRight, Clock, ShieldCheck } from "lucide-react";
import { Button } from "@identitycore/ui";
import { VerificationShell } from "@/components/layout/verification-shell";
import { mockSession } from "@/data/mock-session";

export default function VerificationPortalHome() {
  return (
    <VerificationShell>
      <section className="grid gap-6 lg:grid-cols-[1fr_0.42fr]">
        <div className="rounded-4xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <ShieldCheck className="h-6 w-6" />
          </div>

          <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-5xl">
            Complete your identity verification.
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600 sm:text-base">
            {mockSession.organizationName} is asking you to complete a secure
            IdentityCore workflow for {mockSession.workflowName.toLowerCase()}.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="rounded-xl">
              <Link href={`/session/${mockSession.id}`}>
                Start verification
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>

        <aside className="rounded-4xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <Clock className="h-4 w-4 text-blue-600" />
            Expires in {mockSession.expiresIn}
          </div>

          <div className="mt-6">
            <p className="text-sm font-semibold">Required steps</p>
            <ul className="mt-3 space-y-3 text-sm text-slate-600">
              {mockSession.requirements.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </div>
        </aside>
      </section>
    </VerificationShell>
  );
}
