import type { LucideIcon } from "lucide-react";
import { Button } from "@identitycore/ui";
import { EmptyState } from "./empty-state";
import { PageHeading } from "./page-heading";
import { RichDataTable } from "../table/rich-data-table";


interface ResourcePageProps {
  title: string;
  description: string;
  actionLabel?: string;
  emptyTitle: string;
  emptyDescription: string;
  icon: LucideIcon;
  columns: { key: string; label: string }[];
  rows: Record<string, string>[];
}

export function ResourcePage({
  title,
  description,
  actionLabel,
  emptyTitle,
  emptyDescription,
  icon,
  columns,
  rows,
}: ResourcePageProps) {
  return (
    <div className="space-y-8">
      <PageHeading
        title={title}
        description={description}
        action={
          actionLabel ? (
            <Button className="rounded-xl">{actionLabel}</Button>
          ) : null
        }
      />

      {rows.length > 0 ? (
        <RichDataTable columns={columns} rows={rows} />
      ) : (
        <EmptyState
          icon={icon}
          title={emptyTitle}
          description={emptyDescription}
          actionLabel={actionLabel}
        />
      )}
    </div>
  );
}
