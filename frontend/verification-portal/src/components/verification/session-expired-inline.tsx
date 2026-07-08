import Link from "next/link";
import { ClockAlert } from "lucide-react";
import { Button } from "@identitycore/ui";

export function SessionExpiredInline() {
  return (
    <section className="rounded-[2rem] border border-amber-200 bg-amber-50 p-6 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-amber-700 ring-1 ring-amber-100">
        <ClockAlert className="h-6 w-6" aria-hidden="true" />
      </div>

      <h2 className="mt-5 text-2xl font-semibold tracking-tight text-amber-950">
        Session expired
      </h2>

      <p className="mx-auto mt-2 max-w-md text-sm leading-7 text-amber-800">
        This verification session expired while you were completing the flow.
        Request a new verification link from the organization.
      </p>

      <Button asChild className="mt-6 rounded-xl">
        <Link href="/expired">View expired page</Link>
      </Button>
    </section>
  );
}
