import Link from "next/link";
import { SearchX } from "lucide-react";

export default function NotFound() {
  return (
    <main
      id="main-content"
      className="mx-auto flex min-h-[80vh] max-w-3xl items-center px-4 py-20 text-center sm:px-6"
    >
      <div className="w-full rounded-4xl border border-slate-200 bg-white p-10 shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
          <SearchX className="h-6 w-6" />
        </div>
        <h1 className="mt-6 text-4xl font-semibold tracking-tight">
          Documentation page not found.
        </h1>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          The page may have moved or does not exist yet.
        </p>
        <Link
          href="/"
          className="mt-8 inline-flex rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          Back to docs home
        </Link>
      </div>
    </main>
  );
}
