"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Input, Label } from "@identitycore/ui";
import { loginPlatformAdmin } from "@/lib/admin-api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await loginPlatformAdmin(email, password);
      router.replace("/");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
      <form onSubmit={submit} className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium text-orange-600">IdentityCore</p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-950">Platform Admin sign in</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">Use your authorized IdentityCore staff account.</p>
        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email address</Label>
            <Input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </div>
        </div>
        {error ? <p className="mt-4 text-sm text-red-700" role="alert">{error}</p> : null}
        <Button type="submit" className="mt-6 w-full" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in securely"}
        </Button>
      </form>
    </main>
  );
}
