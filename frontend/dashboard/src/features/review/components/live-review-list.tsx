"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { dashboardApi } from "@/lib/dashboard-api";
export function LiveReviewList() { const [items, setItems] = useState<Array<{ verification_id: string; risk_level: string }>>([]); const [error, setError] = useState(""); useEffect(() => { dashboardApi.manualReviews().then(page => setItems(page.results)).catch(() => setError("Manual-review cases could not be loaded.")); }, []); return <div className="space-y-5"><h1 className="text-2xl font-semibold">Manual review</h1>{error ? <p className="text-red-600">{error}</p> : null}{items.length ? items.map(item => <Link className="block rounded-2xl border bg-white p-4" key={item.verification_id} href={`/manual-review/${item.verification_id}`}>{item.verification_id} · {item.risk_level} risk</Link>) : <p>No cases currently require review.</p>}</div>; }
