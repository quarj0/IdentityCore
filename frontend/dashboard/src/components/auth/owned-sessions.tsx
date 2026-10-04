"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button, Card, CardContent } from "@identitycore/ui";
import { getErrorMessage, restRequest } from "@/lib/api-client";
import { endAuthSession } from "@/lib/logout";

type Session = {
  id: string;
  device_label: string;
  peer_network: string;
  scope: string;
  last_seen_at: string;
  expires_at: string;
  revoked_at: string | null;
  current: boolean;
};

export function OwnedSessions() {
  const router = useRouter();
  const [loadedAt, setLoadedAt] = useState(0);
  const [sessions, setSessions] = useState<Session[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    const data = await restRequest<{ results: Session[] }>("/auth/sessions");
    setSessions(data.results);
    setLoadedAt(Date.now());
  }
  useEffect(() => {
    restRequest<{ results: Session[] }>("/auth/sessions")
      .then((data) => {
        setSessions(data.results);
        setLoadedAt(Date.now());
      })
      .catch((caught) => setError(getErrorMessage(caught)));
  }, []);

  async function revoke(session?: Session) {
    setBusy(true);
    setError("");
    try {
      await restRequest(
        session
          ? `/auth/sessions/${encodeURIComponent(session.id)}/revoke`
          : "/auth/sessions/revoke-others",
        { method: "POST", body: "{}" },
      );
      if (session?.current) {
        try {
          await endAuthSession();
        } finally {
          router.replace("/login");
        }
      } else await load();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardContent className="space-y-4 p-6">
        <h2 className="font-semibold">Your devices and sessions</h2>
        <p className="text-sm text-slate-600">
          Review your recent sign-ins. Revoking a session immediately signs out
          that device. Network addresses are masked.
        </p>
        {error ? <p role="alert">{error}</p> : null}
        {sessions === null ? (
          <p role="status">Loading sessions…</p>
        ) : (
          <>
            <Button
              disabled={busy || !sessions.some((session) => session.current)}
              onClick={() => revoke()}
            >
              Sign out other sessions
            </Button>
            <ul className="space-y-4">
              {sessions.map((session) => {
                const expired = Date.parse(session.expires_at) <= loadedAt;
                return (
                  <li
                    key={session.id}
                    className="space-y-2 border-t border-slate-100 pt-4"
                  >
                    <p className="font-medium">
                      {session.device_label}
                      {session.current ? " · This session" : ""}
                    </p>
                    <p className="text-sm text-slate-600">
                      {session.scope} ·{" "}
                      {session.peer_network || "Network unavailable"} · Last
                      active {new Date(session.last_seen_at).toLocaleString()}
                    </p>
                    {session.revoked_at || expired ? (
                      <p>{session.revoked_at ? "Revoked" : "Expired"}</p>
                    ) : (
                      <Button
                        disabled={busy}
                        onClick={() => revoke(session)}
                        aria-label={`Sign out ${session.device_label}${session.current ? " (this session)" : ""}`}
                      >
                        Sign out
                      </Button>
                    )}
                  </li>
                );
              })}
            </ul>
            {sessions.length === 0 ? <p>No recent sessions.</p> : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
