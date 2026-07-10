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
}: {
  apiOrigin: string;
  getAccessToken?: () => string | null;
  setAccessToken?: (token: string | null) => void;
}) {
  const origin = apiOrigin.replace(/\/$/, "");

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
    if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return parse<T>(await fetch(`${origin}/api/v1${path}`, { ...init, headers, credentials: "include" }));
  }

  async function restoreSession() {
    const data = await rest<{ tokens: { access: string } }>("/auth/refresh", { method: "POST" });
    setAccessToken(data.tokens.access);
    return data.tokens.access;
  }

  async function logout() {
    await rest("/auth/logout", { method: "POST" });
    setAccessToken(null);
  }

  return { rest, restoreSession, logout };
}
