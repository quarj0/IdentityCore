import type { LucideIcon } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

interface NoBackendModulePageProps {
  title: string;
  description: string;
  emptyTitle: string;
  emptyDescription: string;
  icon: LucideIcon;
}

export function NoBackendModulePage({
  title,
  description,
  emptyTitle,
  emptyDescription,
  icon,
}: NoBackendModulePageProps) {
  return (
    <div className="space-y-8">
      <PageHeading title={title} description={description} />
      <EmptyState icon={icon} title={emptyTitle} description={emptyDescription} />
    </div>
  );
}
