"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { Button, Input, Label } from "@identitycore/ui";
import { graphqlRequest } from "@/lib/admin-api";

export default function AcceptPlatformInvitation() {
  const token = useRef("");
  const initialized = useRef(false);
  const [ready, setReady] = useState(false);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    token.current =
      new URLSearchParams(window.location.hash.slice(1)).get("token") ?? "";
    window.history.replaceState(null, "", window.location.pathname);
    setReady(Boolean(token.current));
    if (!token.current)
      setError(
        "This invitation link is missing its credential. Request a new invitation.",
      );
  }, []);
  async function accept(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await graphqlRequest(
        "mutation AcceptPlatformInvitation($token:String!,$password:String!){acceptPlatformAdminInvitation(token:$token,password:$password){user{email} mfaRequired}}",
        { token: token.current, password },
        true,
      );
      token.current = "";
      setPassword("");
      setAccepted(true);
    } catch {
      setError(
        "The invitation could not be accepted. Check its validity and password requirements, or request a new invitation.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
      <section className="w-full max-w-md space-y-5 rounded-3xl border bg-white p-8">
        <h1 className="text-2xl font-semibold">
          Accept platform administrator invitation
        </h1>
        {accepted ? (
          <>
            <p role="status">
              Your account was created. Sign in to complete the required
              security setup.
            </p>
            <Button asChild>
              <Link href="/login">Continue to sign in</Link>
            </Button>
          </>
        ) : (
          <form onSubmit={accept} className="space-y-4">
            <p>
              This grants full platform administration. Use a strong, unique
              password.
            </p>
            <Label htmlFor="invitation-password">New password</Label>
            <Input
              id="invitation-password"
              type="password"
              autoComplete="new-password"
              required
              minLength={12}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <Button type="submit" disabled={!ready || busy}>
              {busy ? "Accepting…" : "Accept invitation"}
            </Button>
          </form>
        )}
        {error ? <p role="alert">{error}</p> : null}
      </section>
    </main>
  );
}
