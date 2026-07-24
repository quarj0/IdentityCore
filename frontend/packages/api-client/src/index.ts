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
  ) { super(message); }
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
    };
    if (sessionScope) headers["X-IdentityCore-Session-Scope"] = sessionScope;
    return headers;
  }

  function refreshAccessToken() {
    if (!refreshInFlight) {
      refreshInFlight = fetch(`${origin}/api/v1/auth/refresh`, {
        method: "POST", credentials: "include",
        headers: authHeaders(),
      }).then((response) => parse<{ tokens: { access: string } }>(response))
        .then((data) => { setAccessToken(data.tokens.access); return data; })
        .finally(() => { refreshInFlight = null; });
    }
    return refreshInFlight;
  }

  async function parse<T>(response: Response): Promise<T> {
    const body = await response.text();
    let payload: ApiSuccess<T> | ApiFailure;
    try {
      payload = JSON.parse(body) as ApiSuccess<T> | ApiFailure;
    } catch {
      throw new IdentityCoreApiError(
        "The service is temporarily unavailable. Please try again shortly.",
        "invalid_response",
        response.status,
      );
    }
    if (!response.ok || !payload.success) {
      const failure = payload as ApiFailure;
      const rawMessage = failure.error?.message ?? "Request failed. Please try again.";
      throw new IdentityCoreApiError(
        /unexpected token|invalidtag|not valid json|json\.parse|syntaxerror/i.test(rawMessage)
          ? "The service is temporarily unavailable. Please try again shortly."
          : rawMessage,
        failure.error?.code,
        response.status,
        failure.request_id,
      );
    }
    return payload.data;
  }

  async function rest<T>(path: string, init: RequestInit = {}) {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (sessionScope) headers.set("X-IdentityCore-Session-Scope", sessionScope);
    if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const send = () => fetch(`${origin}/api/v1${path}`, { ...init, headers, credentials: "include" });
    let response = await send();
    if (response.status === 401 && path !== "/auth/refresh" && path !== "/auth/login") {
      try {
        const refreshed = await refreshAccessToken();
        headers.set("Authorization", `Bearer ${refreshed.tokens.access}`);
        response = await send();
      } catch {
        setAccessToken(null);
      }
    }
    return parse<T>(response);
  }

  async function login(email: string, password: string) {
    const data = await rest<{ tokens: { access: string }; user: unknown }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
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
