import { DocsLayout } from "@/components/docs/docs-layout";

const changes = [
  {
    date: "July 2026",
    title: "Developer portal foundation",
    description:
      "Added quickstart, authentication, API reference, webhooks, sandbox, and examples pages.",
  },
  {
    date: "July 2026",
    title: "Workflow sessions planned",
    description:
      "Defined the first public API shape for creating workflow sessions and receiving webhook results.",
  },
];

export default function ChangelogPage() {
  return (
    <DocsLayout
      title="Changelog"
      description="Track developer-facing changes to IdentityCore APIs, workflow behavior, and documentation."
    >
      <div className="space-y-4">
        {changes.map((change) => (
          <article
            key={change.title}
            className="rounded-3xl border border-slate-200 bg-white p-6"
          >
            <p className="text-sm font-medium text-blue-600">{change.date}</p>
            <h2 className="mt-2 text-xl font-semibold">{change.title}</h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              {change.description}
            </p>
          </article>
        ))}
      </div>
    </DocsLayout>
  );
}
