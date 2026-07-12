"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/feedback/empty-state";
import { TemplateCategoriesCard } from "@/features/templates/components/template-categories-card";
import { TemplateHeader } from "@/features/templates/components/template-header";
import { TemplatePreviewCard } from "@/features/templates/components/template-preview-card";
import { TemplateUsageCard } from "@/features/templates/components/template-usage-card";
import { TemplateVersionCard } from "@/features/templates/components/template-version-card";
import { PageHeader } from "@/components/shared/page-header";
import {
  fetchTemplateRecord,
  type TemplateRecord,
} from "@/features/templates/live-data";

type TemplateDetailPageProps = {
  templateId: string;
};

export function TemplateDetailPage({ templateId }: TemplateDetailPageProps) {
  const [template, setTemplate] = useState<TemplateRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchTemplateRecord(templateId);
        if (active && data) {
          setTemplate(data);
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load template.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [templateId]);

  if (error) {
    return (
      <EmptyState
        title="Unable to load template"
        description={error}
      />
    );
  }

  if (loading && !template) {
    return (
      <PageHeader
        eyebrow="Templates"
        title="Loading template"
        description="Fetching live template data from the backend."
      />
    );
  }

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
          <TemplateVersionCard template={template} />
          <TemplateUsageCard template={template} />
        </div>

        <div className="space-y-4">
          <TemplateCategoriesCard template={template} />
        </div>
      </div>
    </div>
  );
}
