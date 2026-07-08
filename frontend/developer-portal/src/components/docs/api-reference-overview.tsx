import { EndpointCard } from "@/components/docs/endpoint-card";
import { endpoints } from "@/data/endpoints";

const groupedEndpoints = Object.entries(
  endpoints.reduce<Record<string, typeof endpoints>>((groups, endpoint) => {
    if (!groups[endpoint.category]) {
      groups[endpoint.category] = [];
    }

    groups[endpoint.category].push(endpoint);
    return groups;
  }, {}),
);

const methodCount = new Set(endpoints.map((endpoint) => endpoint.method)).size;

export function ApiReferenceOverview() {
  return (
    <>
      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-sm font-medium text-slate-500">Endpoints</p>
          <p className="mt-3 text-3xl font-semibold text-slate-950">
            {endpoints.length}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Route-level reference pages with request and response examples.
          </p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-sm font-medium text-slate-500">API areas</p>
          <p className="mt-3 text-3xl font-semibold text-slate-950">
            {groupedEndpoints.length}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Workflow sessions, verification requests, and events are grouped
            for faster scanning.
          </p>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-sm font-medium text-slate-500">Example styles</p>
          <p className="mt-3 text-3xl font-semibold text-slate-950">
            {methodCount}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Mixed read and write flows with language-specific examples on each
            endpoint page.
          </p>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="text-2xl font-semibold tracking-tight">
          Start with common integration paths
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
          Most teams create a workflow session first, poll or retrieve the
          session during redirects, then subscribe to events for operational
          visibility and async updates.
        </p>
      </section>

      {groupedEndpoints.map(([category, categoryEndpoints]) => (
        <section key={category}>
          <div className="mb-4">
            <h2 className="text-2xl font-semibold tracking-tight">{category}</h2>
            <p className="mt-2 text-sm leading-7 text-slate-600">
              Reference routes and examples for {category.toLowerCase()}.
            </p>
          </div>

          <div className="grid gap-4">
            {categoryEndpoints.map((endpoint) => (
              <EndpointCard key={endpoint.path} {...endpoint} />
            ))}
          </div>
        </section>
      ))}
    </>
  );
}
