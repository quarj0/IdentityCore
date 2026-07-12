import Link from "next/link";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";
import { buildPublicApiUrl } from "@/lib/public-api-docs";

export default function OpenApiPage() {
  return (
    <DocsLayout
      title="OpenAPI spec"
      description="Canonical machine-readable contract for the public IdentityCore API plus workspace-authenticated portal routes. Use this for code generation, contract tests, and future Swagger or Redoc tooling."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Source of truth</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          The browser portal stays lightweight and the backend serves the same
          OpenAPI document that SDKs and tests can consume. If we add a richer
          interactive viewer later, it should read from this spec instead of
          duplicating the contract.
        </p>

        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href={buildPublicApiUrl("/api/v1/docs/openapi.yaml")}
            className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
          >
            Download YAML
          </a>
          <Link
            href="/api-reference"
            className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
          >
            API reference
          </Link>
        </div>
      </section>

      <CodeBlock
        title="Fetch the contract"
        language="bash"
        code={`curl http://localhost:8000/api/v1/docs/openapi.yaml

# production
curl https://api.identitycore.com/api/v1/docs/openapi.yaml`}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">How this helps testing</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>Generate or refresh SDKs from one canonical spec file.</li>
          <li>Validate portal examples against the contract during reviews.</li>
          <li>Use Swagger UI or Redoc later without changing the backend source.</li>
        </ul>
      </section>
    </DocsLayout>
  );
}
