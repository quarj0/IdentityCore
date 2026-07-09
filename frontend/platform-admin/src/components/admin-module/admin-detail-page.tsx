import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { MetricCard } from "@/components/shared/metric-card";
import { SectionCard } from "@/components/shared/section-card";
import { StatusPill } from "@/components/shared/status-pill";
import type { AdminModuleConfig } from "@/components/admin-module/admin-module-types";
import { Activity, BarChart3, Clock3, ShieldCheck } from "lucide-react";

const metricIcons = [Activity, BarChart3, ShieldCheck, Clock3];

type AdminDetailPageProps = {
  id: string;
  config: AdminModuleConfig;
};

export function AdminDetailPage({ id, config }: AdminDetailPageProps) {
  const record = config.getRecord(id);

  if (!record) {
    return (
      <EmptyState
        title="Record not found"
        description="This record may have been removed, archived or moved to another environment."
      />
    );
  }

  const metrics = config.getMetrics(record);
  const sections = config.getSections(record);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav
        aria-label="Breadcrumb"
        className="flex items-center gap-2 text-sm text-slate-500"
      >
        <Link
          href={record.href.split(`/${record.id}`)[0]}
          className="outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          {config.detailBreadcrumbLabel}
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-700">{record.title}</span>
      </nav>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
                {record.title}
              </h1>
              <StatusPill tone={record.statusTone}>{record.status}</StatusPill>
            </div>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              {record.subtitle}
            </p>

            <dl className="mt-5 grid gap-3 sm:grid-cols-4">
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Primary</dt>
                <dd className="mt-1 text-sm font-medium text-slate-950">{record.primaryMeta}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Secondary</dt>
                <dd className="mt-1 text-sm font-medium text-slate-950">{record.secondaryMeta}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Owner</dt>
                <dd className="mt-1 text-sm font-medium text-slate-950">{record.owner}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Updated</dt>
                <dd className="mt-1 text-sm font-medium text-slate-950">{record.updatedAt}</dd>
              </div>
            </dl>
          </div>

          {config.detailActions ? (
            <div className="flex flex-wrap gap-2">{config.detailActions}</div>
          ) : null}
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric, index) => (
          <MetricCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            change={metric.helper}
            trend="neutral"
            helperText="details"
            icon={metricIcons[index] ?? Activity}
          />
        ))}
      </section>

      <div className="grid gap-4 xl:grid-cols-3">
        {sections.map((section, index) => (
          <div
            key={section.title}
            className={index === 0 ? "xl:col-span-2" : undefined}
          >
            <SectionCard
              title={section.title}
              description={section.description}
            >
              <div className="space-y-3">
                {section.items.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                  >
                    <p className="text-sm text-slate-500">{item.label}</p>
                    <p className="mt-2 text-sm font-medium leading-6 text-slate-950">
                      {item.value}
                    </p>
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        ))}
      </div>
    </div>
  );
}