import { ApiReferenceOverview } from "@/components/docs/api-reference-overview";
import { DocsLayout } from "@/components/docs/docs-layout";
import {
  buildPublicApiUrl,
  fetchPublicApiDocsOverview,
} from "@/lib/public-api-docs";

export default async function ApiReferencePage() {
  const overview = await fetchPublicApiDocsOverview();

  return (
    <DocsLayout
      title="API reference"
      description="Core REST endpoints for policies, verifications, evidence reports, and integration workflows."
    >
      {overview?.spec_url ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <h2 className="text-xl font-semibold">Machine-readable contract</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            The OpenAPI spec powers SDK generation, contract tests, and future
            interactive docs.
          </p>
          <div className="mt-5">
            <a
              href={buildPublicApiUrl(overview.spec_url)}
              className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            >
              Download OpenAPI YAML
            </a>
          </div>
        </section>
      ) : null}
      <ApiReferenceOverview overview={overview} />
    </DocsLayout>
  );
}
