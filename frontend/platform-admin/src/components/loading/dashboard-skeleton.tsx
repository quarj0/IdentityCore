import { Skeleton } from "@identitycore/ui";

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="border-b border-slate-200 pb-6">
        <Skeleton className="h-4 w-32 bg-white/10" />
        <Skeleton className="mt-3 h-8 w-80 bg-white/10" />
        <Skeleton className="mt-3 h-4 w-full max-w-2xl bg-white/10" />
      </div>

      <Skeleton className="h-24 rounded-2xl bg-white/10" />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <Skeleton key={index} className="h-36 rounded-2xl bg-white/10" />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Skeleton className="h-80 rounded-2xl bg-white/10 xl:col-span-2" />
        <Skeleton className="h-80 rounded-2xl bg-white/10" />
      </div>
    </div>
  );
}
