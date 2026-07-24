"use client";

import { createIdentityCoreClient, IdentityCoreApiError } from "@identitycore/api-client";
import { getAccessToken, setAccessToken } from "@/lib/auth";
import { getBackendOrigin, getGraphqlApiUrl } from "@/lib/config";

const client = createIdentityCoreClient({
  apiOrigin: getBackendOrigin(),
  getAccessToken,
  setAccessToken,
});

export type PlatformUser = {
  email: string;
  first_name: string;
  last_name: string;
  is_platform_admin: boolean;
};

export async function getCurrentPlatformUser() {
  const response = await client.me<PlatformUser>();
  return response.user;
}

export async function loginPlatformAdmin(email: string, password: string) {
  const response = await client.login(email.trim(), password);
  const user = response.user as PlatformUser;
  if (!user.is_platform_admin) {
    await client.logout();
    throw new IdentityCoreApiError(
      "Invalid email or password.",
      "platform_access_required",
      403,
    );
  }
  return user;
}

export async function logoutPlatformAdmin() {
  await client.logout();
}

type GraphqlResponse<T> = {
  data?: T;
  errors?: Array<{ message: string }>;
};

function buildHeaders(token: string | null) {
  const headers = new Headers({
    Accept: "application/json",
    "Content-Type": "application/json",
  });
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

async function readJson(response: Response) {
  const text = await response.text();
  try {
    return JSON.parse(text) as GraphqlResponse<unknown>;
  } catch {
    throw new IdentityCoreApiError(
      "The service is temporarily unavailable. Please try again shortly.",
      "invalid_response",
      response.status,
    );
  }
}

async function refreshAccessToken() {
  return client.restoreSession();
}

export async function restRequest<T>(
  path: string,
  init: RequestInit = {},
) {
  return client.rest<T>(path, init);
}

export async function graphqlRequest<T>(
  query: string,
  variables?: Record<string, unknown>,
) {
  const send = (token: string | null) =>
    fetch(getGraphqlApiUrl(), {
      method: "POST",
      headers: buildHeaders(token),
      body: JSON.stringify({ query, variables }),
      credentials: "include",
    });

  let response = await send(getAccessToken());
  if (response.status === 401) {
    try {
      const refreshed = await refreshAccessToken();
      response = await send(refreshed);
    } catch {
      setAccessToken(null);
    }
  }

  const payload = (await readJson(response)) as GraphqlResponse<T>;
  if (!response.ok) {
    throw new IdentityCoreApiError(
      "Request failed.",
      "request_failed",
      response.status,
    );
  }

  if (payload.errors?.length) {
    throw new IdentityCoreApiError(
      payload.errors[0]?.message ?? "Request failed.",
      "graphql_error",
      response.status,
    );
  }

  if (!payload.data) {
    throw new IdentityCoreApiError(
      "Response did not include data.",
      "graphql_empty_response",
      response.status,
    );
  }

  return payload.data;
}
