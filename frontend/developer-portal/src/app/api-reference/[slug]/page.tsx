import { notFound } from "next/navigation";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";
import { endpoints } from "@/data/endpoints";

export function generateStaticParams() {
  return endpoints.map((endpoint) => ({
    slug:
      endpoint.path.split("/").filter(Boolean).at(-1)?.replace("{id}", "id") ??
      "endpoint",
  }));
}

export default function ApiDetailPage({
  params,
}: {
  params: { slug: string };
}) {
  const endpoint = endpoints.find((item) =>
    item.path.includes(params.slug === "id" ? "{id}" : params.slug),
  );

  if (!endpoint) notFound();

  return (
    <DocsLayout title={endpoint.title} description={endpoint.description}>
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <p className="text-sm font-semibold text-blue-600">{endpoint.method}</p>
        <code className="mt-3 block break-all rounded-xl bg-slate-100 p-4 text-sm text-slate-700">
          {endpoint.path}
        </code>
      </section>

      <CodeBlock
        title="Request example"
        language="json"
        code={`{
  "workflow": "customer-onboarding",
  "subject": {
    "email": "person@example.com"
  },
  "return_url": "https://app.example.com/complete"
}`}
      />

      <CodeBlock
        title="Response example"
        language="json"
        code={`{
  "id": "wfs_01HZY...",
  "status": "created",
  "verification_url": "https://verify.identitycore.dev/session/wfs_01HZY..."
}`}
      />
    </DocsLayout>
  );
}
