import { Button } from "@identitycore/ui";
import { CloneTemplateDialog } from "@/features/templates/forms/clone-template-dialog";
import { TemplateArchiveDialog } from "@/features/templates/components/template-archive-dialog";
import { TemplatePublishDialog } from "@/features/templates/components/template-publish-dialog";
import { TemplateStatusPill } from "@/features/templates/components/template-status-pill";
import type { TemplateRecord } from "@/features/templates/live-data";

type TemplateHeaderProps = {
  template: TemplateRecord;
};

export function TemplateHeader({ template }: TemplateHeaderProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
              {template.name}
            </h1>
            <TemplateStatusPill status={template.status} />
          </div>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            {template.description}
          </p>

          <dl className="mt-5 grid gap-3 sm:grid-cols-4">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Category</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{template.category}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Version</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{template.version}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Risk</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{template.riskLevel}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Updated</dt>
              <dd className="mt-1 text-sm font-medium text-slate-950">{template.updatedAt}</dd>
            </div>
          </dl>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline">Edit draft</Button>
          <CloneTemplateDialog templateName={template.name} />
          {template.status !== "published" ? (
            <TemplatePublishDialog templateName={template.name} />
          ) : (
            <TemplateArchiveDialog templateName={template.name} />
          )}
        </div>
      </div>
    </section>
  );
}
