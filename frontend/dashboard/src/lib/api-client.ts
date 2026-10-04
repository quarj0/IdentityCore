"use client";

import {
  clearAuthSession,
  getAccessToken,
  notifyAuthSessionExpired,
  setAccessToken,
} from "@/lib/auth";
import { getGraphqlApiUrl, getRestApiBaseUrl } from "@/lib/config";
import { addDashboardSessionScope } from "@/lib/session-scope";

interface ApiSuccess<T> {
  success: true;
  data: T;
  request_id: string;
}

interface ApiErrorPayload {
  success: false;
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
  request_id: string;
}

type ApiEnvelope<T> = ApiSuccess<T> | ApiErrorPayload;
const REQUEST_TIMEOUT_MS = 30_000;
let refreshInFlight: Promise<string> | null = null;

function createRequestId() {
  const value =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : String(Date.now()) + "-" + Math.random().toString(36).slice(2);
  return "req_" + value.replace(/[^a-zA-Z0-9_-]/g, "");
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

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  status: number;
  requestId: string;

  constructor(
    message: string,
    {
      code = "request_failed",
      details = {},
      status = 500,
      requestId = "",
    }: {
      code?: string;
      details?: Record<string, unknown>;
      status?: number;
      requestId?: string;
    } = {},
  ) {
    super(message);
    this.code = code;
    this.details = details;
    this.status = status;
    this.requestId = requestId;
  }
}

function buildHeaders(
  init?: HeadersInit,
  token?: string | null,
  body?: BodyInit | null,
) {
  const headers = addDashboardSessionScope(new Headers(init));
  headers.set("Accept", "application/json");
  headers.set("X-Request-Id", createRequestId());

  if (!(body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return headers;
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
) {
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS,
  );
  const abort = () => controller.abort();
  if (init.signal?.aborted) controller.abort();
  else init.signal?.addEventListener("abort", abort, { once: true });
  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
      cache: "no-store",
    });
  } catch (error) {
    if (init.signal?.aborted) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(
        "The request took too long. Check your connection and try again.",
        {
          code: "request_timeout",
          status: 408,
        },
      );
    }
    throw new ApiError(
      "IdentityCore could not be reached. Check your connection and try again.",
      {
        code: "network_error",
        status: 0,
      },
    );
  } finally {
    window.clearTimeout(timeout);
    init.signal?.removeEventListener("abort", abort);
  }
}

async function fetchWithRetry(input: RequestInfo | URL, init: RequestInit = {}) {
  const method = (init.method ?? "GET").toUpperCase();
  const retrySafe =
    ["GET", "HEAD", "OPTIONS"].includes(method) ||
    Boolean(new Headers(init.headers).get("Idempotency-Key")?.trim());

  for (let attempt = 0; ; attempt += 1) {
    let response: Response;
    try {
      response = await fetchWithTimeout(input, init);
    } catch (error) {
      if (init.signal?.aborted || !retrySafe || attempt >= 1) throw error;
      await new Promise((resolve) => window.setTimeout(resolve, 250));
      continue;
    }
    if (
      !retrySafe ||
      attempt >= 1 ||
      !new Set([408, 425, 429, 502, 503, 504]).has(response.status)
    )
      return response;
    const retryAfterHeader = response.headers.get("Retry-After");
    const retryAfter =
      retryAfterHeader === null ? Number.NaN : Number(retryAfterHeader);
    const delay = Number.isFinite(retryAfter)
      ? Math.min(Math.max(retryAfter * 1000, 0), 1000)
      : 250;
    await new Promise((resolve) => window.setTimeout(resolve, delay));
  }
}

async function parseJson<T>(response: Response, fallbackRequestId = "") {
  const payload = await readJsonResponse<ApiEnvelope<T>>(response, fallbackRequestId);

  if (!response.ok || !payload || payload.success !== true) {
    const code =
      payload && "error" in payload ? payload.error.code : "request_failed";
    const requestId =
      payload && "request_id" in payload
        ? safeRequestId(payload.request_id)
        : safeRequestId(response.headers.get("X-Request-Id")) ||
          safeRequestId(fallbackRequestId);
    throw new ApiError(safeMessage(response.status), {
      code,
      status: response.status,
      requestId,
    });
  }

  return payload.data;
}

async function refreshAccessToken() {
  if (!refreshInFlight) {
    refreshInFlight = fetchWithRetry(`${getRestApiBaseUrl()}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: buildHeaders(),
    })
      .then((response) => parseJson<{ tokens: { access: string } }>(response))
      .then((data) => {
        setAccessToken(data.tokens.access);
        return data.tokens.access;
      })
      .catch((error) => {
        clearAuthSession();
        notifyAuthSessionExpired();
        throw error;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

export async function restRequest<T>(
  path: string,
  init: RequestInit = {},
  options: {
    token?: string | null;
    useAuth?: boolean;
  } = {},
) {
  const token =
    options.token !== undefined
      ? options.token
      : options.useAuth === false
        ? null
        : getAccessToken();

  const send = (access: string | null) =>
    fetchWithRetry(`${getRestApiBaseUrl()}${path}`, {
      ...init,
      credentials: "include",
      headers: buildHeaders(init.headers, access, init.body),
    });
  let response = await send(token);
  if (
    response.status === 401 &&
    options.useAuth !== false &&
    path !== "/auth/refresh"
  ) {
    response = await send(await refreshAccessToken());
  }
  return parseJson<T>(response);
}

interface GraphqlResponse<T> {
  data?: T;
  errors?: Array<{ message: string }>;
}

async function readJsonResponse<T>(
  response: Response,
  fallbackRequestId = "",
): Promise<T> {
  const body = await response.text();
  try {
    return JSON.parse(body) as T;
  } catch {
    throw new ApiError(
      response.status >= 500
        ? "The service is temporarily unavailable. Please try again shortly."
        : "We could not complete your request. Please try again.",
      {
        code: "invalid_response",
        status: response.status,
        requestId:
          safeRequestId(response.headers.get("X-Request-Id")) ||
          safeRequestId(fallbackRequestId),
      },
    );
  }
}

export async function graphqlRequest<T>(
  query: string,
  variables?: Record<string, unknown>,
  options: {
    token?: string | null;
    useAuth?: boolean;
  } = {},
) {
  const token =
    options.token !== undefined
      ? options.token
      : options.useAuth === false
        ? null
        : getAccessToken();

  const send = (access: string | null) =>
    fetchWithRetry(getGraphqlApiUrl(), {
      method: "POST",
      headers: buildHeaders(undefined, access),
      body: JSON.stringify({ query, variables }),
      credentials: "include",
    });
  let response = await send(token);
  if (response.status === 401 && options.useAuth !== false) {
    response = await send(await refreshAccessToken());
  }

  const payload = await readJsonResponse<GraphqlResponse<T>>(response);

  if (!payload || typeof payload !== "object") {
    throw new ApiError(
      "The service returned an unexpected response. Please try again.",
      {
        code: "invalid_response",
        status: response.status,
      },
    );
  }

  if (!response.ok) {
    throw new ApiError("Request failed.", {
      status: response.status,
    });
  }

  if (payload.errors?.length) {
    throw new ApiError("We could not complete your request. Please try again.", {
      code: "graphql_error",
      status: response.status,
      requestId: safeRequestId(response.headers.get("X-Request-Id")),
    });
  }

  if (!payload.data) {
    throw new ApiError("Response did not include data.", {
      code: "graphql_empty_response",
      status: response.status,
    });
  }

  return payload.data;
}

export function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    const message = humanizeErrorMessage(error.message);
    const requestId = safeRequestId(
      "requestId" in error && typeof error.requestId === "string"
        ? error.requestId
        : undefined,
    );
    return requestId ? message + " (Support ID: " + requestId + ")" : message;
  }

  return "Something went wrong. Please try again.";
}

function humanizeErrorMessage(message: string) {
  const technicalError =
    /unexpected token|invalidtag|not valid json|json\.parse|syntaxerror|failed to fetch|networkerror|for update|outer join|traceback|databaseerror|operationalerror|integrityerror|psycopg/i;
  return technicalError.test(message)
    ? "The service is temporarily unavailable. Please try again shortly."
    : message || "Something went wrong. Please try again.";
}
