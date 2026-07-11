"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@identitycore/ui";
import { JsonViewer } from "@/components/dashboard-ui/json-viewer";
import { PageHeading } from "@/components/shared/page-heading";

export function LiveResourceDetail({ title, description, load }: { title: string; description: string; load: () => Promise<Record<string, unknown>> }) {
  const [data,setData]=useState<Record<string,unknown>|null>(null); const [error,setError]=useState("");
  useEffect(()=>{load().then(setData).catch(e=>setError(e instanceof Error?e.message:"Unable to load resource."));},[description]);
  return <div className="space-y-8"><PageHeading title={title} description={description}/>{error?<p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>:null}<Card><CardContent className="p-6">{data?<JsonViewer value={data}/>:<p className="text-sm text-slate-500">Loading...</p>}</CardContent></Card></div>;
}
