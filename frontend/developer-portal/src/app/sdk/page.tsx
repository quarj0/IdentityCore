import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function SdkPage() {
  return (
    <DocsLayout
      title="SDKs"
      description="SDKs are planned client libraries for integrating IdentityCore faster."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Planned SDKs</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>JavaScript / TypeScript</li>
          <li>Python</li>
          <li>PHP</li>
          <li>Java</li>
        </ul>
      </section>

      <CodeBlock
        title="Future TypeScript SDK"
        language="ts"
        code={`const session = await identitycore.workflowSessions.create({
  workflow: "customer-onboarding",
  subject: {
    email: "person@example.com"
  }
});`}
      />
    </DocsLayout>
  );
}
