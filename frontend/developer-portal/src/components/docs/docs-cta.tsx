import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { siteConfig } from "@/lib/site-config";

export function DocsCTA() {
  return (
    <section className="rounded-4xl bg-slate-950 p-8 text-white sm:p-10">
      <h2 className="text-3xl font-semibold tracking-tight">
        Ready to build with IdentityCore?
      </h2>

      <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
        Start in sandbox, test workflow sessions, receive mock webhook events,
        and move toward production when your organization is approved.
      </p>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/quickstart"
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300"
        >
          Start quickstart
          <ArrowRight className="h-4 w-4" />
        </Link>

        <a
          href={siteConfig.createWorkspaceUrl}
          className="inline-flex items-center rounded-xl border border-white/10 px-5 py-3 text-sm font-medium text-white hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300"
        >
          Create workspace
        </a>
      </div>
    </section>
  );
}
