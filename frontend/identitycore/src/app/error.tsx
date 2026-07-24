"use client";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, RefreshCw } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";

export default function GlobalError({ reset }: { reset: () => void }) {
  return (
    <main id="main-content" className="flex min-h-screen items-center bg-slate-50 px-4 py-12 sm:px-6">
      <Card className="mx-auto w-full max-w-xl rounded-3xl border-slate-200 bg-white shadow-sm">
        <CardContent className="p-8 text-center sm:p-10">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
            <AlertTriangle className="size-6" aria-hidden="true" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight">Something went wrong</h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            We could not load this page. Your information has not been changed.
            Please try again or return to the homepage.
          </p>
          <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
            <Button type="button" onClick={reset} className="rounded-xl">
              <RefreshCw className="size-4" />
              Try again
            </Button>
            <Button asChild variant="outline" className="rounded-xl">
              <Link href="/">
                <ArrowLeft className="size-4" />
                Back home
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
