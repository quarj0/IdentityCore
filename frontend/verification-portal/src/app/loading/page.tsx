export default function Loading() {
  return (
    <main id="main-content" className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="space-y-6" aria-live="polite" aria-busy="true">
        <div className="h-32 animate-pulse rounded-4xl bg-slate-200" />
        <div className="h-96 animate-pulse rounded-4xl bg-slate-200" />
      </div>
    </main>
  );
}
