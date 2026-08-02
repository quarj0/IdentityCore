import Link from "next/link";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function CliPage() {
  return (
    <DocsLayout
      title="CLI"
      description="Use the official Python SDK CLI for repeatable, server-side API workflows and automation."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Install and authenticate</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          The CLI is distributed with the Python SDK. Keep credentials on a
          trusted server or CI runner; never embed client secrets in browser or
          mobile applications.
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
        title="Install and use the CLI"
        language="bash"
        code={`pip install identitycore

identitycore login \\
  --api-origin https://api.identitycore.com \\
  --client-id cli_...

identitycore policies list
identitycore verifications list
identitycore verifications create \\
  --purpose "Customer onboarding" \\
  --policy-id pol_... \\
  --full-name "Amina Mensah" \\
  --email amina@example.com`}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Available commands</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>
            <code>health</code> checks API availability.
          </li>
          <li>
            <code>policies list|get</code> reads active verification policies.
          </li>
          <li>
            <code>verifications list|get|create|cancel</code> manages hosted
            verification flows.
          </li>
          <li>Use environment variables for non-interactive CI jobs.</li>
        </ul>
      </section>
    </DocsLayout>
  );
}
