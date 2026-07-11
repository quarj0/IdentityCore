"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";

export function LiveResourceDetail({ title, description, load }: { title: string; description: string; load: () => Promise<Record<string, unknown>> }) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    load().then(setData).catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load resource."));
    // The description changes with the resource ID; callers pass inline loader functions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [description]);

  return (
    <div className="space-y-8">
      <PageHeading title={title} description={description} />
      {error ? <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p> : null}
      <Card><CardContent className="p-6">{data ? (
        <dl className="grid gap-5 sm:grid-cols-2">{Object.entries(data).map(([key, value]) => (
          <div key={key} className={typeof value === "object" ? "sm:col-span-2" : ""}>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{key.replaceAll("_", " ")}</dt>
            <dd className="mt-1 break-words text-sm text-slate-800">{value === null || value === "" ? "—" : typeof value === "object" ? <pre className="overflow-x-auto rounded-xl bg-slate-50 p-4 text-xs leading-6">{JSON.stringify(value, null, 2)}</pre> : String(value)}</dd>
          </div>
        ))}</dl>
      ) : <p className="text-sm text-slate-500">Loading...</p>}</CardContent></Card>
    </div>
  );
}
