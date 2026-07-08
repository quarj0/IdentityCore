import type { ReactNode } from "react";
import { ShieldCheck } from "lucide-react";

interface VerificationShellProps {
  children: ReactNode;
}

export function VerificationShell({ children }: VerificationShellProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-5xl items-center px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold">IdentityCore Verify</p>
              <p className="text-xs text-slate-500">
                Secure verification session
              </p>
            </div>
          </div>
        </div>
      </header>

      <main
        id="main-content"
        className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:py-12"
      >
        {children}
      </main>
    </div>
  );
}
