"use client";

import { AlertTriangle } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardContent className="flex min-h-96 flex-col items-center justify-center p-8 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-700 ring-1 ring-red-100">
          <AlertTriangle className="h-6 w-6" />
        </div>

        <h1 className="mt-6 text-2xl font-semibold">Something went wrong</h1>

        <p className="mt-2 max-w-md text-sm leading-7 text-slate-600">
          The dashboard could not load this view. Try again.
        </p>

        <Button onClick={reset} className="mt-6 rounded-xl">
          Try again
        </Button>
      </CardContent>
    </Card>
  );
}
