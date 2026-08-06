import { Clock, ShieldCheck } from "lucide-react";
import { VerificationShell } from "@/components/layout/verification-shell";

export default function VerificationPortalHome() {
  return (
    <VerificationShell>
      <section className="grid gap-6 lg:grid-cols-[1fr_0.42fr]">
        <div className="rounded-4xl border border-border bg-card p-6 shadow-sm sm:p-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-info/10 text-info ring-1 ring-info/20">
            <ShieldCheck className="h-6 w-6" />
          </div>

          <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-5xl">
            Open your secure verification link.
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-muted-foreground sm:text-base">
            IdentityCore verification sessions are opened from the link sent by
            the requesting organization. If your link expired, ask them to send
            a fresh one.
          </p>
        </div>

        <aside className="rounded-4xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Clock className="h-4 w-4 text-info" />
            Verification links are time limited
          </div>

          <div className="mt-6">
            <p className="text-sm font-semibold">Before you start</p>
            <ul className="mt-3 space-y-3 text-sm text-muted-foreground">
              <li>Use the newest verification link you received.</li>
              <li>Have your identity document ready.</li>
              <li>
                Use a mobile phone for the best camera and liveness experience.
              </li>
            </ul>
          </div>
        </aside>
      </section>
    </VerificationShell>
  );
}
