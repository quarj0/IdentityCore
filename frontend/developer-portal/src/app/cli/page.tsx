import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function CliPage() {
  return (
    <DocsLayout
      title="CLI"
      description="A future command line tool for testing workflows, webhooks, and sandbox events."
    >
      <CodeBlock
        title="Future CLI usage"
        language="bash"
        code={`identitycore login
identitycore workflows list
identitycore sessions create customer-onboarding
identitycore webhooks listen`}
      />
    </DocsLayout>
  );
}
