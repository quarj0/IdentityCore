export interface ApiSuccess<T> {
  success: true;
  data: T;
  request_id: string;
}

export interface ApiFailure {
  success: false;
  error: { code: string; message: string; details?: Record<string, unknown> };
  request_id: string;
}

export class IdentityCoreApiError extends Error {
  constructor(
    message: string,
    public readonly code = "request_failed",
    public readonly status = 500,
    public readonly requestId = "",
  ) {
    super(message);
  }
}

const REQUEST_TIMEOUT_MS = 30_000;
const RETRYABLE_STATUS_CODES = new Set([408, 425, 429, 502, 503, 504]);

function createRequestId() {
  const value =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `req_${value.replace(/[^a-zA-Z0-9_-]/g, "")}`;
}

function safeRequestId(value: string | null | undefined) {
  return value && /^[a-zA-Z0-9_-]{1,80}$/.test(value) ? value : "";
}

function safeMessage(status: number) {
  if (status === 401) return "Your session has expired. Sign in and try again.";
  if (status === 403) return "You do not have permission to complete this action.";
  if (status === 404) return "The requested item could not be found.";
  if (status === 408 || status === 504)
    return "The request took too long. Check your connection and try again.";
  if (status === 429) return "Too many requests. Wait a moment and try again.";
  if (status >= 500 || status === 0)
    return "The service is temporarily unavailable. Please try again shortly.";
  return "We could not complete your request. Check the information and try again.";
}

export function createIdentityCoreClient({
  apiOrigin,
  getAccessToken = () => null,
  setAccessToken = () => undefined,
  sessionScope,
}: {
  apiOrigin: string;
  getAccessToken?: () => string | null;
  setAccessToken?: (token: string | null) => void;
  /** Keeps refresh sessions isolated when multiple first-party apps share an API origin. */
  sessionScope?: "dashboard" | "platform_admin";
}) {
  const origin = apiOrigin.replace(/\/$/, "");
  let refreshInFlight: Promise<{ tokens: { access: string } }> | null = null;

  function authHeaders() {
    const headers: Record<string, string> = {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-Request-Id": createRequestId(),
    };
    if (sessionScope) headers["X-IdentityCore-Session-Scope"] = sessionScope;
    return headers;
  }

  function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    const abort = () => controller.abort();
    init.signal?.addEventListener("abort", abort, { once: true });
    return fetch(input, { ...init, signal: controller.signal, cache: "no-store" })
      .finally(() => {
        clearTimeout(timeout);
        init.signal?.removeEventListener("abort", abort);
      });
  }

  async function fetchWithRetry(input: RequestInfo | URL, init: RequestInit) {
    const method = (init.method ?? "GET").toUpperCase();
    const retrySafe =
      ["GET", "HEAD", "OPTIONS"].includes(method) ||
      new Headers(init.headers).has("Idempotency-Key");
    const requestId = safeRequestId(
      new Headers(init.headers).get("X-Request-Id"),
    );

    for (let attempt = 0; ; attempt += 1) {
      let response: Response;
      try {
        response = await fetchWithTimeout(input, init);
      } catch (error) {
        if (!retrySafe || attempt >= 1) {
          const timedOut = error instanceof DOMException && error.name === "AbortError";
          throw new IdentityCoreApiError(
            safeMessage(timedOut ? 408 : 0),
            timedOut ? "request_timeout" : "network_error",
            timedOut ? 408 : 0,
            requestId,
          );
        }
        await new Promise((resolve) => setTimeout(resolve, 250));
        continue;
      }

      if (!retrySafe || attempt >= 1 || !RETRYABLE_STATUS_CODES.has(response.status))
        return response;

      const retryAfter = Number(response.headers.get("Retry-After"));
      const delay = Number.isFinite(retryAfter)
        ? Math.min(Math.max(retryAfter * 1000, 0), 1000)
        : 250;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  function refreshAccessToken() {
    if (!refreshInFlight) {
      const headers = authHeaders();
      const requestId = headers["X-Request-Id"];
      refreshInFlight = fetchWithRetry(`${origin}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers,
      })
        .then((response) =>
          parse<{ tokens: { access: string } }>(response, requestId),
        )
        .then((data) => {
          setAccessToken(data.tokens.access);
          return data;
        })
        .finally(() => {
          refreshInFlight = null;
        });
    }
    return refreshInFlight;
  }

  async function parse<T>(
    response: Response,
    fallbackRequestId = "",
  ): Promise<T> {
    const body = await response.text();
    let payload: ApiSuccess<T> | ApiFailure;
    try {
      payload = JSON.parse(body) as ApiSuccess<T> | ApiFailure;
    } catch {
      throw new IdentityCoreApiError(
        safeMessage(response.status),
        "invalid_response",
        response.status,
        safeRequestId(response.headers.get("X-Request-Id")) ||
          safeRequestId(fallbackRequestId),
      );
    }
    if (!response.ok || !payload.success) {
      const failure = payload as ApiFailure;
      throw new IdentityCoreApiError(
        safeMessage(response.status),
        failure.error?.code ?? "request_failed",
        response.status,
        safeRequestId(
          failure.request_id ||
            response.headers.get("X-Request-Id") ||
            fallbackRequestId,
        ),
      );
    }
    return payload.data;
  }

  async function rest<T>(path: string, init: RequestInit = {}) {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    headers.set("X-Request-Id", createRequestId());
    if (sessionScope) headers.set("X-IdentityCore-Session-Scope", sessionScope);
    if (init.body && !headers.has("Content-Type"))
      headers.set("Content-Type", "application/json");
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const requestId = headers.get("X-Request-Id") ?? "";
    const send = () =>
      fetchWithRetry(`${origin}/api/v1${path}`, {
        ...init,
        headers,
        credentials: "include",
      });
    let response = await send();
    if (
      response.status === 401 &&
      path !== "/auth/refresh" &&
      path !== "/auth/login"
    ) {
      try {
        const refreshed = await refreshAccessToken();
        headers.set("Authorization", `Bearer ${refreshed.tokens.access}`);
        response = await send();
      } catch {
        setAccessToken(null);
      }
    }
    return parse<T>(response, requestId);
  }

  async function login(email: string, password: string) {
    const data = await rest<{ tokens: { access: string }; user: unknown }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
    );
    setAccessToken(data.tokens.access);
    return data;
  }

  async function me<T = unknown>() {
    return rest<{ user: T }>("/auth/me");
  }

  async function restoreSession() {
    const data = await refreshAccessToken();
    return data.tokens.access;
  }

  async function logout() {
    await rest("/auth/logout", { method: "POST" });
    setAccessToken(null);
  }

  return { rest, restoreSession, login, me, logout };
}
