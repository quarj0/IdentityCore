"use client";

import { clearAuthSession, getAccessToken, setAccessToken } from "@/lib/auth";
import { getGraphqlApiUrl, getRestApiBaseUrl } from "@/lib/config";

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
let refreshInFlight: Promise<string> | null = null;

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  status: number;

  constructor(
    message: string,
    {
      code = "request_failed",
      details = {},
      status = 500,
    }: {
      code?: string;
      details?: Record<string, unknown>;
      status?: number;
    } = {},
  ) {
    super(message);
    this.code = code;
    this.details = details;
    this.status = status;
  }
}

function buildHeaders(init?: HeadersInit, token?: string | null, body?: BodyInit | null) {
  const headers = new Headers(init);
  headers.set("Accept", "application/json");

  if (!(body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return headers;
}

async function parseJson<T>(response: Response) {
  const payload = await readJsonResponse<ApiEnvelope<T>>(response);

  if (!response.ok || !payload || payload.success !== true) {
    const message =
      payload && "error" in payload
        ? payload.error.message
        : "The request could not be processed.";
    const code = payload && "error" in payload ? payload.error.code : "request_failed";
    const details = payload && "error" in payload ? payload.error.details : {};
    throw new ApiError(message, {
      code,
      details,
      status: response.status,
    });
  }

  return payload.data;
}

async function refreshAccessToken() {
  if (!refreshInFlight) {
    refreshInFlight = fetch(`${getRestApiBaseUrl()}/auth/refresh`, {
      method: "POST", credentials: "include",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
    }).then((response) => parseJson<{ tokens: { access: string } }>(response))
      .then((data) => { setAccessToken(data.tokens.access); return data.tokens.access; })
      .catch((error) => { clearAuthSession(); throw error; })
      .finally(() => { refreshInFlight = null; });
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

  const send = (access: string | null) => fetch(`${getRestApiBaseUrl()}${path}`, {
    ...init,
    credentials: "include",
    headers: buildHeaders(init.headers, access, init.body),
  });
  let response = await send(token);
  if (response.status === 401 && options.useAuth !== false && path !== "/auth/refresh") {
    response = await send(await refreshAccessToken());
  }
  return parseJson<T>(response);
}

interface GraphqlResponse<T> {
  data?: T;
  errors?: Array<{ message: string }>;
}

async function readJsonResponse<T>(response: Response): Promise<T> {
  const body = await response.text();
  try {
    return JSON.parse(body) as T;
  } catch {
    throw new ApiError(
      response.status >= 500
        ? "The service is temporarily unavailable. Please try again shortly."
        : "We could not complete your request. Please try again.",
      { code: "invalid_response", status: response.status },
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

  const send = (access: string | null) => fetch(getGraphqlApiUrl(), {
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
    throw new ApiError("The service returned an unexpected response. Please try again.", {
      code: "invalid_response",
      status: response.status,
    });
  }

  if (!response.ok) {
    throw new ApiError("Request failed.", {
      status: response.status,
    });
  }

  if (payload.errors?.length) {
    throw new ApiError(payload.errors[0]?.message ?? "Request failed.", {
      code: "graphql_error",
      details: { errors: payload.errors },
      status: response.status,
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
  if (error instanceof ApiError) {
    return humanizeErrorMessage(error.message);
  }

  if (error instanceof Error) {
    return humanizeErrorMessage(error.message);
  }

  return "Something went wrong. Please try again.";
}

function humanizeErrorMessage(message: string) {
  const technicalError =
    /unexpected token|invalidtag|not valid json|json\.parse|syntaxerror|failed to fetch|networkerror/i;
  return technicalError.test(message)
    ? "The service is temporarily unavailable. Please try again shortly."
    : message || "Something went wrong. Please try again.";
}
