import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";
import {
  buildPublicApiUrl,
  fetchPublicApiDocsOverview,
} from "@/lib/public-api-docs";

const statusLabels: Record<string, string> = {
  ready: "Ready",
  in_progress: "In progress",
  not_started: "Not started",
};

export default async function SdkPage() {
  const overview = await fetchPublicApiDocsOverview();
  const sdkStatus = overview?.sdk_status ?? [];

  return (
    <DocsLayout
      title="SDKs"
      description="Integrate IdentityCore with production-ready Python, JavaScript, Java, and .NET client libraries."
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Current SDK status</h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
              The backend publishes the current SDK matrix so the portal always
              reflects what is actually available.
            </p>
          </div>

          {overview?.spec_url ? (
            <a
              href={buildPublicApiUrl(overview.spec_url)}
              className="inline-flex items-center rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
            >
              OpenAPI spec
            </a>
          ) : null}
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {sdkStatus.map((sdk) => (
            <div
              key={sdk.language}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex items-center justify-between gap-4">
                <h3 className="text-sm font-semibold capitalize text-slate-950">
                  {sdk.language}
                </h3>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200">
                  {statusLabels[sdk.status] ?? sdk.status}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-600">{sdk.notes}</p>
              <p className="mt-3 text-xs uppercase tracking-wide text-slate-400">
                {sdk.path}
              </p>
            </div>
          ))}
        </div>
      </section>

      <CodeBlock
        title="Python SDK"
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
        <h2 className="text-xl font-semibold">What ships now</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 text-slate-600">
          <li>
            Python, JavaScript, Java, and .NET SDKs are implemented, tested, and
            tracked by the backend docs metadata.
          </li>
          <li>
            Each SDK supports policies, hosted verifications, safe retries,
            request IDs, idempotent creation, and webhook signature verification.
          </li>
          <li>
            The OpenAPI spec is the source of truth for generated clients, tests,
            and future portal tooling.
          </li>
        </ul>
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

      <CodeBlock
        title="Java SDK"
        language="java"
        code={`import io.identitycore.IdentityCoreClient;

var client = IdentityCoreClient.builder()
    .apiOrigin("https://api.identitycore.com")
    .clientId("cli_...")
    .clientSecret("...")
    .build();

var policies = client.policies().list();
var verification = client.verifications().create(
    "Customer onboarding",
    policies.get(0).get("id").asText(),
    Map.of(
        "full_name", "Kwame Mensah",
        "email", "kwame@example.com"
    ),
    "customer_123"
);

System.out.println(verification.get("verification_url").asText());`}
      />

      <CodeBlock
        title=".NET SDK"
        language="csharp"
        code={`using IdentityCore;

using var client = new IdentityCoreClient(new IdentityCoreOptions
{
    ApiOrigin = new Uri("https://api.identitycore.com"),
    ClientId = "cli_...",
    ClientSecret = "...",
});

var policies = await client.Policies.ListAsync();
var verification = await client.Verifications.CreateAsync(
    purpose: "Customer onboarding",
    policyId: policies[0].GetProperty("id").GetString()!,
    verificationSubject: new
    {
        full_name = "Kwame Mensah",
        email = "kwame@example.com",
    },
    externalReference: "customer_123");

Console.WriteLine(verification.GetProperty("verification_url").GetString());`}
      />
    </DocsLayout>
  );
}

