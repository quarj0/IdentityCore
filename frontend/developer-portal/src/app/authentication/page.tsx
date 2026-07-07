import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function AuthenticationPage() {
  return (
    <DocsLayout
      title="Authentication"
      description="IdentityCore APIs use bearer API keys scoped to your workspace and environment."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">API keys</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          Use sandbox keys for testing and production keys only after your
          organization is approved.
        </p>
      </section>

      <CodeBlock
        title="Authorization header"
        language="http"
        code={`Authorization: Bearer sk_test_xxxxxxxxxxxxx`}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Key safety</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>Never expose secret keys in frontend code.</li>
          <li>
            Rotate keys when team members leave or secrets may be exposed.
          </li>
          <li>Use separate keys for sandbox and production.</li>
          <li>
            Restrict production access until organization approval is complete.
          </li>
        </ul>
      </section>
    </DocsLayout>
  );
}
