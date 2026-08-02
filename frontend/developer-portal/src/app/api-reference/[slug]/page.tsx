import { notFound } from "next/navigation";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";
import { LanguageExamples } from "@/components/docs/language-examples";
import { endpoints } from "@/data/endpoints";
import {
  buildPublicApiUrl,
  fetchPublicApiDocsOverview,
} from "@/lib/public-api-docs";

export function generateStaticParams() {
  return endpoints.map((endpoint) => ({
    slug: endpoint.slug,
  }));
}

export default async function ApiDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const endpoint = endpoints.find((item) => item.slug === slug);

  if (endpoint) {
    return (
      <DocsLayout title={endpoint.title} description={endpoint.description}>
        <section className="rounded-3xl border border-slate-200 bg-white p-6">
          <p className="text-sm font-semibold text-blue-600">
            {endpoint.method}
          </p>

          <code className="mt-3 block break-all rounded-xl bg-slate-100 p-4 text-sm text-slate-700">
            {endpoint.path}
          </code>
        </section>

        <CodeBlock
          title="Request example"
          language={endpoint.method === "GET" ? "http" : "json"}
          code={endpoint.request}
        />

        <CodeBlock
          title="Response example"
          language="json"
          code={endpoint.response}
        />

        <LanguageExamples
          title="Examples by language"
          description="Use the same endpoint from the stack your team is already shipping."
          examples={endpoint.examples}
        />
      </DocsLayout>
    );
  }

  const overview = await fetchPublicApiDocsOverview();
  const contractEndpoint = overview?.resources.find(
    (resource) => resource.slug === slug,
  );

  if (!contractEndpoint) {
    notFound();
  }

  const contractPath = contractEndpoint.path.startsWith("/api/")
    ? contractEndpoint.path
    : `/api/v1${contractEndpoint.path}`;

  return (
    <DocsLayout
      title={contractEndpoint.name}
      description={contractEndpoint.description}
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <p className="text-sm font-semibold text-blue-600">
          {contractEndpoint.method}
        </p>

        <code className="mt-3 block break-all rounded-xl bg-slate-100 p-4 text-sm text-slate-700">
          {contractPath}
        </code>
      </section>

      <CodeBlock
        title="Request template"
        language="bash"
        code={`curl -X ${contractEndpoint.method} https://api.identitycore.com${contractPath} \\
  -H "Authorization: Bearer $IDENTITYCORE_API_KEY" \\
  -H "X-Client-Id: $IDENTITYCORE_CLIENT_ID"`}
      />

      <CodeBlock
        title="Response envelope"
        language="json"
        code={`{
  "success": true,
  "data": {},
  "request_id": "req_01JABC..."
}`}
      />

      <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6">
        <h2 className="text-xl font-semibold text-amber-950">
          Contract reference
        </h2>
        <p className="mt-3 text-sm leading-7 text-amber-900">
          This route is published in the canonical OpenAPI contract. Use the
          contract for the exact request schema, response fields, authentication
          requirements, and available operations.
        </p>
        <a
          href={buildPublicApiUrl(
            overview?.spec_url ?? "/api/v1/docs/openapi.yaml",
          )}
          className="mt-5 inline-flex rounded-xl bg-amber-900 px-4 py-2 text-sm font-medium text-white hover:bg-amber-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-900"
        >
          Open the OpenAPI contract
        </a>
      </section>
    </DocsLayout>
  );
}
