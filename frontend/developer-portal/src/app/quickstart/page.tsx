import { CodeBlock } from "@/components/docs/code-block"; 
import { DocsCTA } from "@/components/docs/docs-cta";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function QuickstartPage() {
  return (
    <DocsLayout
      title="Quickstart"
      description="Create your first workflow session and receive a hosted verification URL."
    >
      <CodeBlock
        title="Create a workflow session"
        language="bash"
        code={`curl -X POST https://api.identitycore.dev/api/v1/workflow-sessions \\
  -H "Authorization: Bearer sk_test_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "workflow": "customer-onboarding",
    "subject": {
      "email": "person@example.com"
    },
    "return_url": "https://app.example.com/complete"
  }'`}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">What happens next?</h2>
        <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>IdentityCore creates a workflow session.</li>
          <li>
            Your application redirects the user to the hosted verification URL.
          </li>
          <li>The user completes the workflow.</li>
          <li>IdentityCore sends a webhook event with the result.</li>
        </ol>
      </section>

      <DocsCTA />
    </DocsLayout>
  );
}
