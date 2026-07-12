import Link from "next/link";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function CliPage() {
  return (
    <DocsLayout
      title="CLI roadmap"
      description="The command line workflow is not shipped yet, so this page documents the intended shape rather than pretending the tool already exists."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">What to use today</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          For now, use the API reference, the OpenAPI spec, and the SDKs to
          exercise the public API. That keeps testing grounded in the same
          contract that the backend publishes.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            href="/api-reference"
            className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
          >
            API reference
          </Link>
          <Link
            href="/openapi"
            className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
          >
            OpenAPI spec
          </Link>
          <Link
            href="/sdk"
            className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
          >
            SDKs
          </Link>
        </div>
      </section>

      <CodeBlock
        title="Planned CLI surface"
        language="bash"
        code={`identitycore login
identitycore policies list
identitycore verifications create customer-onboarding
identitycore webhooks listen`}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">How we should build it later</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>Generate the CLI from the OpenAPI contract where practical.</li>
          <li>Keep authentication and environment selection explicit.</li>
          <li>Use the same backend test fixtures as the portal and SDK docs.</li>
        </ul>
      </section>
    </DocsLayout>
  );
}
