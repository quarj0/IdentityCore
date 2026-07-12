import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function CliPage() {
  return (
    <DocsLayout
      title="CLI"
      description="A future command line tool for testing verifications, webhooks, and sandbox events."
    >
      <CodeBlock
        title="Future CLI usage"
        language="bash"
        code={`identitycore login
identitycore policies list
identitycore verifications create customer-onboarding
identitycore webhooks listen`}
      />
    </DocsLayout>
  );
}
