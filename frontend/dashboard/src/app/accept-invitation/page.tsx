"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { restRequest } from "@/lib/api-client";

export default function AcceptInvitationPage() {
  const token = useRef("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [pending, setPending] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const received = new URLSearchParams(window.location.hash.slice(1)).get(
      "token",
    );
    if (received) token.current = received;
    window.history.replaceState(null, "", window.location.pathname);
  }, []);
  async function accept(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await restRequest(
        "/auth/team/invitations/accept",
        {
          method: "POST",
          body: JSON.stringify({
            token: token.current,
            password,
            mfa_code: code,
          }),
        },
        { useAuth: false },
      );
      token.current = "";
      setPassword("");
      setCode("");
      setAccepted(true);
    } catch {
      setError(
        "The invitation could not be accepted. Check your password and MFA code, or ask your administrator for a new invitation.",
      );
    } finally {
      setPending(false);
    }
  }
  return (
    <main className="mx-auto max-w-lg space-y-5 p-8" id="main-content">
      <h1 className="text-2xl font-semibold">Accept your team invitation</h1>
      {accepted ? (
        <p>
          Your invitation was accepted.{" "}
          <Link href="/login">Sign in to continue</Link>.
        </p>
      ) : (
        <form onSubmit={accept} className="space-y-4">
          <p>
            If you already have an account, enter your current password.
            Otherwise choose a strong new password. Accounts stay within their
            existing organization.
          </p>
          <label className="block">
            Password
            <input
              className="mt-1 block w-full rounded border p-2"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <label className="block">
            MFA or recovery code, if enabled
            <input
              className="mt-1 block w-full rounded border p-2"
              autoComplete="one-time-code"
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
          </label>
          {error && <p role="alert">{error}</p>}
          <button className="rounded border px-4 py-2" disabled={pending}>
            {pending ? "Accepting…" : "Accept invitation"}
          </button>
        </form>
      )}
    </main>
  );
}
