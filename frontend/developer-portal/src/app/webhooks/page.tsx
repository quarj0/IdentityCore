import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function WebhooksPage() {
  return (
    <DocsLayout
      title="Webhooks"
      description="Receive event notifications when workflow sessions complete, fail, require review, or expire."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Common events</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>workflow.session.created</li>
          <li>workflow.session.completed</li>
          <li>workflow.session.failed</li>
          <li>workflow.session.review_required</li>
          <li>workflow.session.expired</li>
        </ul>
      </section>

      <CodeBlock
        title="Webhook payload"
        language="json"
        code={`{
  "id": "evt_01HZY...",
  "type": "workflow.session.completed",
  "created_at": "2026-07-07T12:00:00Z",
  "data": {
    "session_id": "wfs_01HZY...",
    "decision": "approved"
  }
}`}
      />
    </DocsLayout>
  );
}
