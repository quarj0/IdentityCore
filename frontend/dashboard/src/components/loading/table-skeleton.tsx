export function TableSkeleton() {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4">
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, index) => (
          <div
            key={index}
            className="h-12 animate-pulse rounded-2xl bg-slate-100"
          />
        ))}
      </div>
    </div>
  );
}
