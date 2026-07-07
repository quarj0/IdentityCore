import { workflowTemplates } from "@/data/templates";
import { TemplateCard } from "@/components/marketing/template-card";

interface RelatedTemplatesProps {
  currentSlug: string;
  category: string;
}

export function RelatedTemplates({
  currentSlug,
  category,
}: RelatedTemplatesProps) {
  const related = workflowTemplates
    .filter(
      (template) =>
        template.slug !== currentSlug && template.category === category,
    )
    .slice(0, 3);

  const fallback = workflowTemplates
    .filter((template) => template.slug !== currentSlug)
    .slice(0, 3);

  const templates = related.length > 0 ? related : fallback;

  return (
    <section className="bg-slate-50 py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="max-w-3xl">
          <p className="text-sm font-medium text-blue-600">
            Related templates
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            Explore more workflows.
          </h2>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <TemplateCard key={template.slug} {...template} />
          ))}
        </div>
      </div>
    </section>
  );
}