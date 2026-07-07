import { notFound } from "next/navigation";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";
import { endpoints } from "@/data/endpoints";

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

  if (!endpoint) {
    notFound();
  }

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
        language={endpoint.method === "GET" ? "http" : "json"}
        code={endpoint.request}
      />

      <CodeBlock
        title="Response example"
        language="json"
        code={endpoint.response}
      />
    </DocsLayout>
  );
}
