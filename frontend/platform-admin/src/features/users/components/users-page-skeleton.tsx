import { Skeleton } from "@identitycore/ui";

export function UsersPageSkeleton() {
  return (
    <div className="space-y-6 bg-white text-slate-950">
      <div className="border-b border-slate-200 pb-6">
        <Skeleton className="h-4 w-32 bg-slate-100" />
        <Skeleton className="mt-3 h-8 w-80 bg-slate-100" />
        <Skeleton className="mt-3 h-4 w-full max-w-2xl bg-slate-100" />
      </div>

      <Skeleton className="h-20 rounded-3xl bg-slate-100" />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-36 rounded-3xl bg-slate-100" />
        ))}
      </div>

      <Skeleton className="h-96 rounded-3xl bg-slate-100" />
    </div>
  );
}
