import Link from "next/link";
import { SearchX } from "lucide-react";
import { Button } from "@identitycore/ui";
import { VerificationShell } from "@/components/layout/verification-shell";

export default function NotFound() {
  return (
    <VerificationShell>
      <div className="mx-auto max-w-xl rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
          <SearchX className="h-6 w-6" />
        </div>

        <h1 className="mt-6 text-3xl font-semibold tracking-tight">
          Verification page not found
        </h1>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          The verification page you are looking for does not exist or may have
          been removed.
        </p>

        <Button asChild className="mt-6 rounded-xl">
          <Link href="/">Back home</Link>
        </Button>
      </div>
    </VerificationShell>
  );
}
