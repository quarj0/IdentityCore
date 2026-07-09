import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { TemplateCategoriesCard } from "@/features/templates/components/template-categories-card";
import { TemplateHeader } from "@/features/templates/components/template-header";
import { TemplatePreviewCard } from "@/features/templates/components/template-preview-card";
import { TemplateUsageCard } from "@/features/templates/components/template-usage-card";
import { TemplateVersionCard } from "@/features/templates/components/template-version-card";
import { getTemplateById } from "@/features/templates/mock-data";

type TemplateDetailPageProps = {
  templateId: string;
};

export function TemplateDetailPage({ templateId }: TemplateDetailPageProps) {
  const template = getTemplateById(templateId);

  if (!template) {
    return (
      <EmptyState
        title="Template not found"
        description="This template may have been archived, deleted or moved to another environment."
      />
    );
  }

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-slate-500">
        <Link
          href="/templates"
          className="outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          Templates
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-700">{template.name}</span>
      </nav>

      <TemplateHeader template={template} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <TemplatePreviewCard template={template} />
          <TemplateVersionCard />
          <TemplateUsageCard />
        </div>

        <div className="space-y-4">
          <TemplateCategoriesCard template={template} />
        </div>
      </div>
    </div>
  );
}