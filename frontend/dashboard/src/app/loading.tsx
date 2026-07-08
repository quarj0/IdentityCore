export default function Loading() {
  return (
    <div className="space-y-6" aria-live="polite" aria-busy="true">
      <div className="h-10 w-64 animate-pulse rounded-xl bg-slate-200" />
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="h-36 animate-pulse rounded-3xl bg-slate-200"
          />
        ))}
      </div>
      <div className="h-96 animate-pulse rounded-3xl bg-slate-200" />
    </div>
  );
}
