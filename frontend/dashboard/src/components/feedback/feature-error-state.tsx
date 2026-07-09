"use client";

import { AlertTriangle, Copy } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";

export function FeatureErrorState({ reset }: { reset: () => void }) {
  const errorId = "err_mock_01";

  return (
    <Card className="rounded-3xl border-red-200 bg-white shadow-sm">
      <CardContent className="flex min-h-96 flex-col items-center justify-center p-8 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-700 ring-1 ring-red-100">
          <AlertTriangle className="h-6 w-6" />
        </div>

        <h1 className="mt-6 text-2xl font-semibold">
          This view could not load
        </h1>

        <p className="mt-2 max-w-md text-sm leading-7 text-slate-600">
          Try again or copy the error ID when contacting support.
        </p>

        <p className="mt-3 rounded-xl bg-slate-100 px-3 py-2 text-xs text-slate-600">
          Error ID: {errorId}
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Button onClick={reset} className="rounded-xl">
            Try again
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={() => navigator.clipboard.writeText(errorId)}
            className="rounded-xl"
          >
            <Copy className="h-4 w-4" />
            Copy error ID
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
