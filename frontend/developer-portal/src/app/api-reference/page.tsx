import { DocsLayout } from "@/components/docs/docs-layout";
import { EndpointCard } from "@/components/docs/endpoint-card";
import { endpoints } from "@/data/endpoints";

export default function ApiReferencePage() {
  return (
    <DocsLayout
      title="API reference"
      description="Core REST endpoints for workflow sessions, verification requests, events, and integration workflows."
    >
      <div className="grid gap-4">
        {endpoints.map((endpoint) => (
          <EndpointCard key={endpoint.path} {...endpoint} />
        ))}
      </div>
    </DocsLayout>
  );
}
