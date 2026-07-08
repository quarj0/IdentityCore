import { ApiReferenceOverview } from "@/components/docs/api-reference-overview";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function ApiReferencePage() {
  return (
    <DocsLayout
      title="API reference"
      description="Core REST endpoints for workflow sessions, verification requests, events, and integration workflows."
    >
      <ApiReferenceOverview />
    </DocsLayout>
  );
}
