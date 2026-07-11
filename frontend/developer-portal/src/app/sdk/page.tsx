import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";

export default function SdkPage() {
  return (
    <DocsLayout
      title="SDKs"
      description="Use IdentityCore SDKs to create and monitor hosted verification requests from your backend."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Python SDK</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          The first public SDK is Python. It authenticates with API-client
          credentials and wraps the public verification and policy/template APIs.
        </p>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>
            Send <code>X-Client-Id</code> and <code>Authorization: Bearer</code>{" "}
            headers automatically.
          </li>
          <li>List active verification templates before creating a request.</li>
          <li>Create, retrieve, cancel, resend, and inspect verification evidence URLs.</li>
        </ul>
      </section>

      <CodeBlock
        title="Create a hosted verification"
        language="python"
        code={`from identitycore import IdentityCoreClient

client = IdentityCoreClient(
    api_origin="https://api.identitycore.com",
    client_id="cli_...",
    client_secret="...",
)

policies = client.policies.list()

verification = client.verifications.create(
    purpose="Customer onboarding",
    policy_id=policies[0]["id"],
    verification_subject={
        "full_name": "Kwame Mensah",
        "email": "kwame@example.com",
    },
    external_reference="customer_123",
)

print(verification["verification_url"])`}
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">Scopes</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li><code>policies:read</code> lists active templates.</li>
          <li><code>verifications:create</code> creates, cancels, and resends links.</li>
          <li><code>verifications:read</code> reads verification status and evidence URLs.</li>
        </ul>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold">JavaScript and Postman</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          A JavaScript SDK and focused Postman public API collection are available
          in the repository under <code>sdk/javascript</code> and{" "}
          <code>sdk/postman</code>. Both follow the same public REST contract as
          the Python SDK.
        </p>
      </section>

      <CodeBlock
        title="JavaScript SDK"
        language="js"
        code={`import { IdentityCoreClient } from "@identitycore/sdk";

const client = new IdentityCoreClient({
  apiOrigin: "https://api.identitycore.com",
  clientId: "cli_...",
  clientSecret: "...",
});

const policies = await client.policies.list();

const verification = await client.verifications.create({
  purpose: "Customer onboarding",
  policyId: policies[0].id,
  verificationSubject: {
    fullName: "Kwame Mensah",
    email: "kwame@example.com",
  },
  externalReference: "customer_123",
});

console.log(verification.verification_url);`}
      />
    </DocsLayout>
  );
}
