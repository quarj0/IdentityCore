"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import { safeLog } from "@identitycore/api-client";
import { Button } from "@identitycore/ui";
import { VerificationShell } from "@/components/layout/verification-shell";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    safeLog("error", "verification_portal_render_error", {
      error_name: error.name,
      error_message: error.message,
      digest: error.digest ?? "",
    });
  }, [error]);

  return (
    <VerificationShell>
      <div className="mx-auto max-w-xl rounded-4xl border border-border bg-card p-8 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
          <AlertTriangle className="h-6 w-6" />
        </div>

        <h1 className="mt-6 text-3xl font-semibold tracking-tight">
          Something went wrong
        </h1>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          The verification portal hit an unexpected error. Your evidence was not
          lost — try again, and if this keeps happening, contact the
          organization that sent you this link.
        </p>
        {error.digest ? (
          <p className="mt-4 text-xs text-muted-foreground">
            Reference {error.digest}
          </p>
        ) : null}

        <Button onClick={reset} className="mt-6 rounded-xl">
          Try again
        </Button>
      </div>
    </VerificationShell>
  );
}
