import { DocsLayout } from "@/components/docs/docs-layout";

export default function SandboxPage() {
  return (
    <DocsLayout
      title="Sandbox"
      description="Use the sandbox environment to test live API flows before requesting production access."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Sandbox behavior</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          Sandbox mode lets you test API keys, verifications, hosted links,
          webhook events, and verification outcomes without processing real
          identity evidence.
        </p>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Common outcomes</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>approved</li>
          <li>rejected</li>
          <li>review_required</li>
          <li>expired</li>
        </ul>
      </section>
    </DocsLayout>
  );
}
