import Link from "next/link";

interface EndpointCardProps {
  slug: string;
  method: string;
  path: string;
  title: string;
  description: string;
}

export function EndpointCard({
  slug,
  method,
  path,
  title,
  description,
}: EndpointCardProps) {
  return (
    <Link
      href={`/api-reference/${slug}`}
      className="block rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
    >
      <div className="flex flex-wrap items-center gap-3">
        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 ring-1 ring-blue-100">
          {method}
        </span>

        <code className="break-all rounded-lg bg-slate-100 px-2 py-1 text-sm text-slate-700">
          {path}
        </code>
      </div>

      <h2 className="mt-5 font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>

      <p className="mt-5 text-sm font-medium text-blue-600">View endpoint →</p>
    </Link>
  );
}
