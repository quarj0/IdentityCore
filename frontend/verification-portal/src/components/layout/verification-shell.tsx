"use client";

import type { ReactNode } from "react";
import { ShieldCheck } from "lucide-react";
import { ThemeToggle } from "@identitycore/ui";
import { usePortalLocale } from "@/lib/portal-locale";
import { localizeText } from "@/lib/i18n";

interface VerificationShellProps {
  children: ReactNode;
}

export function VerificationShell({ children }: VerificationShellProps) {
  const locale = usePortalLocale();
  const t = (text: string) => localizeText(locale, text);
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-info text-info-foreground">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold">
                {t("IdentityCore Verify")}
              </p>
              <p className="text-xs text-muted-foreground">
                {t("Secure verification session")}
              </p>
            </div>
          </div>
          <ThemeToggle
            labels={{
              light: t("Switch to light theme"),
              dark: t("Switch to dark theme"),
              toggle: t("Toggle theme"),
            }}
          />
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
