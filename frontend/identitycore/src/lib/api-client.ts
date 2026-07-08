"use client";

import { getAccessToken } from "@/lib/auth";
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

function buildHeaders(init?: HeadersInit, token?: string | null) {
  const headers = new Headers(init);
  headers.set("Accept", "application/json");

  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return headers;
}

async function parseJson<T>(response: Response) {
  const payload = (await response.json()) as ApiEnvelope<T>;

  if (!response.ok || !payload.success) {
    const message =
      "error" in payload
        ? payload.error.message
        : "The request could not be processed.";
    const code = "error" in payload ? payload.error.code : "request_failed";
    const details = "error" in payload ? payload.error.details : {};
    throw new ApiError(message, {
      code,
      details,
      status: response.status,
    });
  }

  return payload.data;
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

  const response = await fetch(`${getRestApiBaseUrl()}${path}`, {
    ...init,
    headers: buildHeaders(init.headers, token),
  });

  return parseJson<T>(response);
}

interface GraphqlResponse<T> {
  data?: T;
  errors?: Array<{ message: string }>;
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

  const response = await fetch(getGraphqlApiUrl(), {
    method: "POST",
    headers: buildHeaders(undefined, token),
    body: JSON.stringify({ query, variables }),
  });

  const payload = (await response.json()) as GraphqlResponse<T>;

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
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}
