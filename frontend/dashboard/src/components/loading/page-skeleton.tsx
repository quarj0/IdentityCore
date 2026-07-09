import { CardSkeleton } from "./card-skeleton";
import { TableSkeleton } from "./table-skeleton";

export function PageSkeleton() {
  return (
    <div className="space-y-8" aria-live="polite" aria-busy="true">
      <div className="h-10 w-72 animate-pulse rounded-xl bg-slate-200" />
      <div className="grid gap-6 md:grid-cols-3">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
      <TableSkeleton />
    </div>
  );
}
