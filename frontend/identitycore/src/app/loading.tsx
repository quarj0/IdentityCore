export default function Loading() {
  return (
    <main id="main-content" className="min-h-screen bg-background" aria-busy="true" aria-live="polite">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:py-20">
        <span className="sr-only">Loading page</span>
        <div className="h-5 w-32 animate-pulse rounded bg-slate-200" />
        <div className="mt-6 h-12 max-w-2xl animate-pulse rounded bg-slate-200" />
        <div className="mt-4 h-6 max-w-xl animate-pulse rounded bg-slate-100" />
        <div className="mt-10 grid gap-6 lg:grid-cols-3">
          {[0, 1, 2].map((item) => (
            <div key={item} className="h-52 animate-pulse rounded-3xl border border-slate-200 bg-slate-100" />
          ))}
        </div>
      </div>
    </main>
  );
}
