import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function WebhooksPage() {
  return (
    <DocsLayout
      title="Webhooks"
      description="Receive event notifications when verifications complete, fail, require review, or expire."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Common events</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>verification.created</li>
          <li>verification.consent_accepted</li>
          <li>verification.document_uploaded</li>
          <li>verification.selfie_uploaded</li>
          <li>verification.manual_review_required</li>
          <li>verification.verified</li>
          <li>verification.rejected</li>
          <li>verification.expired</li>
          <li>verification.cancelled</li>
        </ul>
      </section>

      <CodeBlock
        title="Webhook payload"
        language="json"
        code={`{
  "id": "evt_01HZY...",
  "type": "verification.verified",
  "created_at": "2026-07-07T12:00:00Z",
  "data": {
    "verification_id": "ver_01HZY...",
    "status": "verified"
  }
}`}
      />
    </DocsLayout>
  );
}
