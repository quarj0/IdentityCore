"use client";

import { FormEvent, useState } from "react";
import { Loader2 } from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@identitycore/ui";
import { useDashboardSession } from "@/components/auth/dashboard-session";

export default function DashboardLoginPage() {
  const { login } = useDashboardSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true); setError("");
    try { await login(String(form.get("email")), String(form.get("password"))); }
    catch { setError("We could not sign you in. Check your email and password."); }
    finally { setBusy(false); }
  }

  return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-4"><Card className="w-full max-w-md rounded-3xl"><CardHeader><CardTitle>Sign in to your workspace</CardTitle></CardHeader><CardContent><form onSubmit={submit} className="space-y-4"><div><Label htmlFor="email">Email</Label><Input id="email" name="email" type="email" required /></div><div><Label htmlFor="password">Password</Label><Input id="password" name="password" type="password" required /></div>{error ? <p className="text-sm text-red-600">{error}</p> : null}<Button className="w-full" disabled={busy}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}Sign in</Button></form></CardContent></Card></main>;
}
