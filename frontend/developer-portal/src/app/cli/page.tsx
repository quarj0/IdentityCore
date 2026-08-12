import Link from "next/link";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function CliPage() {
  return (
    <DocsLayout
      title="CLI"
      description="Manage every IdentityCore environment and resource from a terminal or CI runner."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Install and authenticate</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          The CLI ships with the dependency-free Python SDK. Named profiles keep
          sandbox and production settings separate. Keep credentials on a
          trusted server or CI runner—never in browser or mobile code.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          {[
            ["API reference", "/api-reference"],
            ["OpenAPI spec", "/openapi"],
            ["SDKs", "/sdk"],
          ].map(([label, href]) => (
            <Link
              key={href}
              href={href}
              className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            >
              {label}
            </Link>
          ))}
        </div>
      </section>

      <CodeBlock
        title="Install, configure profiles, and query resources"
        language="bash"
        code={`pip install identitycore

identitycore login --profile sandbox --environment sandbox \\
  --access-token "$IDENTITYCORE_ACCESS_TOKEN"
identitycore login --profile production --environment production \\
  --access-token "$IDENTITYCORE_ACCESS_TOKEN"

identitycore --profile sandbox --output table projects list
identitycore --profile sandbox verifications list --status pending --limit 50
identitycore --profile sandbox verifications create \\
  --purpose "Customer onboarding" --policy-id pol_... \\
  --full-name "Amina Mensah" --email amina@example.com`}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Complete command surface</h2>
        <div className="mt-4 grid gap-4 text-sm leading-7 text-slate-600 md:grid-cols-2">
          <ul className="list-disc space-y-2 pl-5">
            <li>
              <code>projects list|get|create|enable|disable</code>
            </li>
            <li>
              <code>api-clients list|get|create|rotate|revoke</code>
            </li>
            <li>
              <code>
                workflows list|get|create|publish|archive|clone|versions
              </code>
            </li>
            <li>
              <code>templates list|get</code>
            </li>
          </ul>
          <ul className="list-disc space-y-2 pl-5">
            <li>
              <code>webhooks list|get|create|test|disable|reactivate</code>
            </li>
            <li>
              <code>verifications list|get|create|cancel|evidence</code>
            </li>
            <li>
              <code>policies list|get</code>
            </li>
            <li>
              <code>profiles list|current|delete</code>
            </li>
          </ul>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Automation and output</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>
            Use <code>--output json</code> for stable machine-readable output or{" "}
            <code>--output table</code> for terminal-friendly results.
          </li>
          <li>
            List commands expose only the pagination and filtering options
            supported by their corresponding public endpoint.
          </li>
          <li>
            CI can use <code>IDENTITYCORE_ACCESS_TOKEN</code> or client
            credential environment variables without prompts. Errors are JSON on
            stderr.
          </li>
          <li>
            Enable autocomplete with <code>identitycore completion bash</code>,{" "}
            <code>zsh</code>, or <code>fish</code>.
          </li>
        </ul>
      </section>

      <CodeBlock
        title="Webhook testing and evidence downloads"
        language="bash"
        code={`identitycore --profile sandbox webhooks create \\
  --url https://example.com/hooks/identitycore \\
  --event verification.completed --event verification.failed
identitycore --profile sandbox webhooks test wh_...
identitycore --profile sandbox verifications evidence ver_... \\
  --pdf --file ./evidence/ver_....pdf`}
      />
    </DocsLayout>
  );
}
