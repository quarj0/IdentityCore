import { ApiReferenceOverview } from "@/components/docs/api-reference-overview";
import { DocsLayout } from "@/components/docs/docs-layout";
import { fetchPublicApiDocsOverview } from "@/lib/public-api-docs";

export default async function ApiReferencePage() {
  const overview = await fetchPublicApiDocsOverview();

  return (
    <DocsLayout
      title="API reference"
      description="Core REST endpoints for policies, verifications, evidence reports, and integration workflows."
    >
      <ApiReferenceOverview overview={overview} />
    </DocsLayout>
  );
}
