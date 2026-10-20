"use client";

const API_BASE = "/api/verification";
const REQUEST_TIMEOUT_MS = 30_000;
const credentialExchanges = new Map<
  string,
  { token: string; promise: Promise<void> }
>();

export async function consumeSessionCredentials(sessionId: string) {
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const fragmentToken = hash.get("token");
  const pending = credentialExchanges.get(sessionId);
  if (pending && (!fragmentToken || pending.token === fragmentToken)) {
    await pending.promise;
    return { sessionId };
  }
  if (fragmentToken) {
    const promise = (async () => {
      const controller = new AbortController();
      const timeout = window.setTimeout(
        () => controller.abort(),
        REQUEST_TIMEOUT_MS,
      );
      try {
        const response = await fetch(`${API_BASE}/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sessionId, sessionToken: fragmentToken }),
          signal: controller.signal,
        });
        if (!response.ok || (await response.json()).success !== true)
          throw new Error(
            "The secure verification credential could not be accepted. Please retry this link.",
          );
        const current = new URLSearchParams(
          window.location.hash.replace(/^#/, ""),
        );
        if (current.get("token") === fragmentToken) {
          window.history.replaceState(
            null,
            "",
            window.location.pathname + window.location.search,
          );
        }
      } finally {
        window.clearTimeout(timeout);
      }
    })();
    const entry = { token: fragmentToken, promise };
    credentialExchanges.set(sessionId, entry);
    try {
      await promise;
    } finally {
      if (credentialExchanges.get(sessionId) === entry)
        credentialExchanges.delete(sessionId);
    }
  }
  return { sessionId };
}

export function clearSessionCredentials(sessionId: string) {
  void fetch(`${API_BASE}/session`, {
    method: "DELETE",
    headers: { "X-Session-Id": sessionId },
    keepalive: true,
  });
}
