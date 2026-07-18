import type { ReactNode } from "react";
import {
  BadgeCheck,
  Building2,
  FileCheck2,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";

import { VerificationProgress } from "./verification-progress";

interface VerificationFrameProps {
  organizationName: string;
  organizationLogoUrl?: string;
  purpose: string;
  currentStep: string;
  reference: string;
  children: ReactNode;
}

export function VerificationFrame({
  organizationName,
  organizationLogoUrl,
  purpose,
  currentStep,
  reference,
  children,
}: VerificationFrameProps) {
  return (
    <div className="verification-page min-h-screen">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-sm shadow-blue-200">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-semibold tracking-tight text-slate-950">
                IdentityCore Verify
              </p>
              <p className="text-xs text-slate-500">Secure identity verification</p>
            </div>
          </div>
          <div className="hidden items-center gap-2 text-xs font-medium text-slate-500 sm:flex">
            <LockKeyhole className="h-4 w-4 text-emerald-600" aria-hidden="true" />
            Encrypted session
          </div>
        </div>
      </header>

      <main id="main-content" className="mx-auto grid max-w-6xl gap-8 px-4 py-7 sm:px-6 lg:grid-cols-[19rem_minmax(0,1fr)] lg:py-12">
        <aside className="space-y-5 lg:sticky lg:top-8 lg:self-start">
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Verification requested by
            </p>
            <div className="mt-4 flex items-center gap-3">
              {organizationLogoUrl ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={organizationLogoUrl}
                  alt=""
                  className="h-11 w-11 rounded-2xl border border-slate-200 bg-white object-contain p-1.5"
                />
              ) : (
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-600">
                  <Building2 className="h-5 w-5" aria-hidden="true" />
                </span>
              )}
              <div className="min-w-0">
                <h1 className="truncate text-sm font-semibold text-slate-950">
                  {organizationName}
                </h1>
                <p className="mt-0.5 line-clamp-2 text-xs leading-5 text-slate-500">
                  {purpose}
                </p>
              </div>
            </div>
          </section>

          <VerificationProgress currentStep={currentStep} />

          <section className="rounded-3xl border border-blue-100 bg-blue-50/70 p-5">
            <div className="flex gap-3">
              <BadgeCheck className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" aria-hidden="true" />
              <div>
                <h2 className="text-sm font-semibold text-blue-950">Your data stays protected</h2>
                <p className="mt-1.5 text-xs leading-5 text-blue-900/70">
                  Evidence is encrypted, access is audited, and it is used only for this verification.
                </p>
              </div>
            </div>
          </section>

          <div className="flex items-center gap-2 px-1 text-xs text-slate-400">
            <FileCheck2 className="h-3.5 w-3.5" aria-hidden="true" />
            Reference {reference}
          </div>
        </aside>

        <section className="min-w-0">{children}</section>
      </main>
    </div>
  );
}
