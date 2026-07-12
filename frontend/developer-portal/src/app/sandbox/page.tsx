import Link from "next/link";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

const safeRoutes = [
  "/projects/",
  "/api-clients/",
  "/verifications/",
  "/verifications/{verification_id}",
  "/verifications/{verification_id}/resend-link",
  "/verifications/{verification_id}/evidence-report",
  "/verifications/{verification_id}/evidence-report/download",
  "/verifications/{verification_id}/evidence-report/download.pdf",
  "/webhook-endpoints/",
  "/webhook-endpoints/{webhook_id}/test",
  "/organization/me/",
  "/organization/me/verification-documents/upload/",
  "/organization/me/verification-documents/{document_id}/complete/",
  "/organization/me/verification-documents/{document_id}/",
  "/uploads/",
  "/uploads/{upload_id}/transfer",
  "/verifications/manual-reviews",
  "/verifications/manual-reviews/{verification_id}/decision",
];

export default function SandboxPage() {
  return (
    <DocsLayout
      title="Sandbox"
      description="Use a sandbox project and sandbox API client to test live API flows safely before requesting production access."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Create a sandbox project</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          Sandbox projects isolate test traffic, limit side effects, and give
          you a place to create test-only API clients and webhook endpoints.
          This repo also creates a default sandbox project automatically when a
          workspace has none.
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
        </div>

        <CodeBlock
          title="Create or inspect projects"
          language="bash"
          code={`GET /api/v1/projects/
POST /api/v1/projects/

# create a sandbox project
{
  "name": "Sandbox",
  "slug": "sandbox",
  "environment": "sandbox",
  "allowed_origins": []
}`}
        />
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Mint a sandbox API client</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          Most portals issue a dedicated sandbox API client, and this codebase
          does the same. Pending workspaces can create one sandbox test key and
          use it for verification testing without production permissions.
        </p>

        <CodeBlock
          title="Create a sandbox key"
          language="json"
          code={`POST /api/v1/api-clients/
{
  "project_id": "prj_...",
  "name": "Sandbox test key",
  "scopes": ["verifications:read", "verifications:create"],
  "allowed_networks": [],
  "rate_limit_per_minute": 30
}`}
        />

        <p className="mt-4 text-sm leading-7 text-slate-600">
          The backend enforces the sandbox limit and scope trimming for pending
          workspaces, so the portal can safely show this as the default testing
          path.
        </p>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Routes safe for test runs</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          Use these routes when you want to exercise the product without touching
          real customer verification data.
        </p>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {safeRoutes.map((route) => (
            <div
              key={route}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700"
            >
              {route}
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Typical test flow</h2>
        <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>Create or choose a sandbox project.</li>
          <li>Mint a sandbox API client with `verifications:read` and `verifications:create`.</li>
          <li>Create a verification and use the hosted link to complete the flow.</li>
          <li>Inspect webhook delivery, manual review, and evidence-report routes.</li>
          <li>Upload supporting documents through the organization verification form.</li>
        </ol>
      </section>
    </DocsLayout>
  );
}
