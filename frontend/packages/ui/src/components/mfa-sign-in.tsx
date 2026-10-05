"use client";

import { useState, type FormEvent } from "react";
import { Button } from "./button";
import { Input } from "./input";
import { Label } from "./label";

export interface MfaTransaction {
  mfa_required: true;
  mfa_enrollment_required: boolean;
  mfa_token: string;
}

// Transaction proofs, setup secrets and recovery codes stay in component memory.
export function MfaSignIn<T extends { recovery_codes?: string[] }>({
  transaction,
  request,
  onComplete,
  onCancel,
}: {
  transaction: MfaTransaction;
  request: <R>(path: string, body: Record<string, string>) => Promise<R>;
  onComplete: (result: T) => void;
  onCancel: () => void;
}) {
  const [secret, setSecret] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [result, setResult] = useState<T | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const enrollment = transaction.mfa_enrollment_required;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const body = { mfa_token: transaction.mfa_token, code: code.trim() };
      if (enrollment && !secret) {
        const setup = await request<{ secret: string }>(
          "/auth/mfa/enroll",
          body,
        );
        setSecret(setup.secret);
      } else {
        const completed = await request<T>(
          enrollment ? "/auth/mfa/enroll/confirm" : "/auth/mfa/challenge",
          body,
        );
        setCode("");
        setSecret(null);
        if (enrollment) setResult(completed);
        else onComplete(completed);
      }
    } catch {
      setError(
        "Verification failed. Check your code or restart sign in if the transaction expired.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (result)
    return (
      <section className="space-y-4" aria-label="Recovery codes">
        <h2 className="text-lg font-semibold">Save your recovery codes</h2>
        <p>
          Store these codes privately. Each can be used once if you lose your
          authenticator.
        </p>
        <ul className="space-y-2 font-mono break-all">
          {result.recovery_codes?.map((value) => (
            <li key={value}>{value}</li>
          ))}
        </ul>
        <Button
          type="button"
          onClick={() => {
            setResult(null);
            onComplete(result);
          }}
        >
          I saved my recovery codes
        </Button>
      </section>
    );

  return (
    <form className="space-y-4" onSubmit={submit}>
      <h2 className="text-lg font-semibold">
        {enrollment ? "Set up your authenticator" : "Verify your sign in"}
      </h2>
      {enrollment ? (
        <p>
          Add the setup key to your authenticator, then enter its six-digit
          code.
        </p>
      ) : (
        <p>Enter an authenticator code or an unused recovery code.</p>
      )}
      {secret ? (
        <p className="font-mono break-all" aria-label="Authenticator setup key">
          {secret}
        </p>
      ) : null}
      {!enrollment || secret ? (
        <div className="space-y-2">
          <Label htmlFor="mfa-code">Authentication code</Label>
          <Input
            id="mfa-code"
            autoComplete="one-time-code"
            autoCapitalize="none"
            spellCheck={false}
            maxLength={64}
            value={code}
            required
            onChange={(event) => setCode(event.target.value)}
          />
        </div>
      ) : null}
      {error ? (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      ) : null}
      <Button type="submit" disabled={busy}>
        {busy
          ? "Please wait…"
          : enrollment && !secret
            ? "Generate setup key"
            : "Verify"}
      </Button>
      <Button
        type="button"
        variant="outline"
        disabled={busy}
        onClick={onCancel}
      >
        Restart sign in
      </Button>
    </form>
  );
}
