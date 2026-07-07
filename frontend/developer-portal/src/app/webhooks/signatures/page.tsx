import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function WebhookSignaturesPage() {
  return (
    <DocsLayout
      title="Webhook signatures"
      description="Verify that webhook events were sent by IdentityCore before trusting them."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Recommended behavior</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>Read the raw webhook request body.</li>
          <li>Compare the signature header with your computed HMAC.</li>
          <li>Reject events with invalid signatures.</li>
          <li>Ignore duplicate event IDs.</li>
        </ul>
      </section>

      <CodeBlock
        title="Signature header"
        language="http"
        code={`IdentityCore-Signature: t=1783440000,v1=signature_hash`}
      />
    </DocsLayout>
  );
}
