import type { LucideIcon } from "lucide-react";
import { Button, Card, CardContent } from "@identitycore/ui";

interface EmptyStateProps {
  title: string;
  description: string;
  icon: LucideIcon;
  actionLabel?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  actionLabel,
}: EmptyStateProps) {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardContent className="flex min-h-80 flex-col items-center justify-center p-8 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <Icon className="h-6 w-6" aria-hidden="true" />
        </div>

        <h2 className="mt-6 text-xl font-semibold">{title}</h2>

        <p className="mt-2 max-w-md text-sm leading-7 text-slate-600">
          {description}
        </p>

        {actionLabel ? (
          <Button className="mt-6 rounded-xl">{actionLabel}</Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
