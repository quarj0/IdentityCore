import { Download, KeyRound, Play, Search } from "lucide-react";
import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";
import { InteractiveApiReference } from "@/components/docs/interactive-api-reference";
import { buildPublicApiUrl } from "@/lib/public-api-docs";

const capabilities = [
  { icon: Search, title: "Find every operation", text: "Filter by path, title, or tag and expand an operation to inspect its parameters and schemas." },
  { icon: Play, title: "Send a request", text: "Choose Try it out, enter your values, and execute the call against the selected API server." },
  { icon: KeyRound, title: "Authorize once", text: "Use Authorize to add your sandbox API secret and client ID to requests during this browser session." },
];

export default function OpenApiPage() {
  return (
    <DocsLayout
      title="Interactive API reference"
      description="Explore the complete IdentityCore REST contract. Every operation includes authentication, parameters, request schemas, response schemas, status codes, and an in-browser request console."
    >
      <section className="grid gap-4 md:grid-cols-3">
        {capabilities.map(({ icon: Icon, title, text }) => (
          <article key={title} className="rounded-2xl border border-slate-200 bg-white p-5">
            <Icon className="h-5 w-5 text-blue-600" aria-hidden="true" />
            <h2 className="mt-4 font-semibold text-slate-950">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
          </article>
        ))}
      </section>

      <section className="rounded-2xl border border-blue-200 bg-blue-50 p-5 text-sm leading-6 text-blue-950">
        <strong>Use sandbox credentials.</strong> Requests run from your browser and can create or update data. Select a sandbox server and never paste a production secret on a shared device.
      </section>

      <InteractiveApiReference />

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold">Use the contract in your tools</h2>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">
              Import the OpenAPI 3.1 document into Postman, Insomnia, Bruno, or your code generator. The interactive reference and downloadable file use the same contract.
            </p>
          </div>
          <a href={buildPublicApiUrl("/api/v1/docs/openapi.yaml")} className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800">
            <Download className="h-4 w-4" aria-hidden="true" /> Download YAML
          </a>
        </div>
      </section>

      <CodeBlock title="Generate a typed client" language="bash" code={`npx @openapitools/openapi-generator-cli generate \\\n  -i https://api.identitycore.com/api/v1/docs/openapi.yaml \\\n  -g typescript-fetch \\\n  -o ./identitycore-client`} />
    </DocsLayout>
  );
}
